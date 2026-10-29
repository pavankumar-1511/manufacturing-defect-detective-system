import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.config import settings
from app.models.inspection import Inspection
from app.database.mongodb import (
    is_mongo_enabled,
    get_mongo_inspections_collection,
    MongoInspectionRecord,
    ping_mongo,
)
from app.schemas.inspection import (
    DashboardStats,
    DefectDistributionItem,
    TrendPoint,
)
from app.services.inference.detector import pipeline

logger = logging.getLogger("db_repo")

class DatabaseRepository:
    """
    Unified Data Access Layer supporting both MongoDB Atlas (NoSQL)
    and SQLite / PostgreSQL (SQLAlchemy ORM).
    """

    @staticmethod
    def is_connected(db: Optional[Session] = None) -> bool:
        if is_mongo_enabled():
            return ping_mongo()
        return True

    @staticmethod
    def get_dashboard_stats(db: Optional[Session] = None) -> DashboardStats:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            total = col.count_documents({})
            if total == 0:
                return DashboardStats(
                    total_inspections=0,
                    accepted_count=0,
                    defective_count=0,
                    review_required_count=0,
                    defect_percentage=0.0,
                    manual_review_percentage=0.0,
                    avg_inference_time_ms=0.0,
                )
            accepted = col.count_documents({"status": "ACCEPTED"})
            defective = col.count_documents({"status": "DEFECTIVE"})
            review = col.count_documents({"status": "REVIEW_REQUIRED"})

            pipeline_avg = [
                {"$group": {"_id": None, "avg_duration": {"$avg": "$inference_duration_ms"}}}
            ]
            res = list(col.aggregate(pipeline_avg))
            avg_duration = res[0]["avg_duration"] if res and "avg_duration" in res[0] else 0.0

            return DashboardStats(
                total_inspections=total,
                accepted_count=accepted,
                defective_count=defective,
                review_required_count=review,
                defect_percentage=round((defective / total) * 100.0, 1),
                manual_review_percentage=round((review / total) * 100.0, 1),
                avg_inference_time_ms=round(float(avg_duration or 0.0), 1),
            )
        else:
            total = db.query(Inspection).count()
            if total == 0:
                return DashboardStats(
                    total_inspections=0,
                    accepted_count=0,
                    defective_count=0,
                    review_required_count=0,
                    defect_percentage=0.0,
                    manual_review_percentage=0.0,
                    avg_inference_time_ms=0.0,
                )
            accepted = db.query(Inspection).filter(Inspection.status == "ACCEPTED").count()
            defective = db.query(Inspection).filter(Inspection.status == "DEFECTIVE").count()
            review = db.query(Inspection).filter(Inspection.status == "REVIEW_REQUIRED").count()
            avg_duration = db.query(func.avg(Inspection.inference_duration_ms)).scalar() or 0.0

            return DashboardStats(
                total_inspections=total,
                accepted_count=accepted,
                defective_count=defective,
                review_required_count=review,
                defect_percentage=round((defective / total) * 100.0, 1),
                manual_review_percentage=round((review / total) * 100.0, 1),
                avg_inference_time_ms=round(float(avg_duration), 1),
            )

    @staticmethod
    def get_trends(days: int = 7, db: Optional[Session] = None) -> List[TrendPoint]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days - 1)
        trend_map = {}
        for i in range(days):
            d = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            trend_map[d] = {"date": d, "total": 0, "accepted": 0, "defective": 0, "review": 0}

        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            docs = col.find({"created_at": {"$gte": start_date}}).sort("created_at", 1)
            for doc in docs:
                created = doc.get("created_at")
                if isinstance(created, datetime):
                    d_str = created.strftime("%Y-%m-%d")
                elif isinstance(created, str):
                    d_str = created[:10]
                else:
                    continue
                if d_str in trend_map:
                    trend_map[d_str]["total"] += 1
                    status = doc.get("status")
                    if status == "ACCEPTED":
                        trend_map[d_str]["accepted"] += 1
                    elif status == "DEFECTIVE":
                        trend_map[d_str]["defective"] += 1
                    elif status == "REVIEW_REQUIRED":
                        trend_map[d_str]["review"] += 1
        else:
            records = (
                db.query(Inspection)
                .filter(Inspection.created_at >= start_date)
                .order_by(Inspection.created_at.asc())
                .all()
            )
            for item in records:
                d_str = item.created_at.strftime("%Y-%m-%d")
                if d_str in trend_map:
                    trend_map[d_str]["total"] += 1
                    if item.status == "ACCEPTED":
                        trend_map[d_str]["accepted"] += 1
                    elif item.status == "DEFECTIVE":
                        trend_map[d_str]["defective"] += 1
                    elif item.status == "REVIEW_REQUIRED":
                        trend_map[d_str]["review"] += 1

        return [TrendPoint(**v) for v in trend_map.values()]

    @staticmethod
    def get_defect_distribution(db: Optional[Session] = None) -> List[DefectDistributionItem]:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            total_defects = col.count_documents({"defect_type": {"$ne": None, "$exists": True}})
            if total_defects == 0:
                return [DefectDistributionItem(category=cat, count=0, percentage=0.0) for cat in pipeline.SUPPORTED_CATEGORIES]

            pipe = [
                {"$match": {"defect_type": {"$ne": None, "$exists": True}}},
                {"$group": {"_id": "$defect_type", "count": {"$sum": 1}}}
            ]
            agg = list(col.aggregate(pipe))
            found_cats = set()
            results = []
            for item in agg:
                cat = item["_id"]
                cnt = item["count"]
                if cat:
                    found_cats.add(cat)
                    results.append(DefectDistributionItem(
                        category=cat,
                        count=cnt,
                        percentage=round((cnt / total_defects) * 100.0, 1)
                    ))
            for cat in pipeline.SUPPORTED_CATEGORIES:
                if cat not in found_cats:
                    results.append(DefectDistributionItem(category=cat, count=0, percentage=0.0))
            return results
        else:
            total_defects = db.query(Inspection).filter(Inspection.defect_type.isnot(None)).count()
            if total_defects == 0:
                return [DefectDistributionItem(category=cat, count=0, percentage=0.0) for cat in pipeline.SUPPORTED_CATEGORIES]

            distribution = (
                db.query(Inspection.defect_type, func.count(Inspection.id))
                .filter(Inspection.defect_type.isnot(None))
                .group_by(Inspection.defect_type)
                .all()
            )
            results = []
            found_cats = set()
            for cat, cnt in distribution:
                if cat:
                    found_cats.add(cat)
                    results.append(DefectDistributionItem(
                        category=cat,
                        count=cnt,
                        percentage=round((cnt / total_defects) * 100.0, 1)
                    ))
            for cat in pipeline.SUPPORTED_CATEGORIES:
                if cat not in found_cats:
                    results.append(DefectDistributionItem(category=cat, count=0, percentage=0.0))
            return results

    @staticmethod
    def save_inspection(inspection_data: Dict[str, Any], db: Optional[Session] = None) -> Any:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            # Ensure created_at is datetime
            if "created_at" not in inspection_data or not inspection_data["created_at"]:
                inspection_data["created_at"] = datetime.now(timezone.utc)
            col.insert_one(inspection_data)
            return MongoInspectionRecord(inspection_data)
        else:
            db_item = Inspection(
                id=inspection_data.get("id"),
                original_filename=inspection_data.get("original_filename"),
                stored_filename=inspection_data.get("stored_filename"),
                annotated_filename=inspection_data.get("annotated_filename"),
                product_id=inspection_data.get("product_id"),
                status=inspection_data.get("status"),
                defect_type=inspection_data.get("defect_type"),
                confidence_score=inspection_data.get("confidence_score"),
                model_name=inspection_data.get("model_name"),
                model_version=inspection_data.get("model_version"),
                inference_duration_ms=inspection_data.get("inference_duration_ms", 0.0),
                manual_review_required=inspection_data.get("manual_review_required", False),
                inspection_notes=inspection_data.get("inspection_notes"),
                defect_regions=inspection_data.get("defect_regions"),
                created_at=inspection_data.get("created_at") or datetime.now(timezone.utc)
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            return db_item

    @staticmethod
    def get_inspection_by_id(inspection_id: str, db: Optional[Session] = None) -> Optional[Any]:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            doc = col.find_one({"id": inspection_id})
            if not doc:
                return None
            return MongoInspectionRecord(doc)
        else:
            return db.query(Inspection).filter(Inspection.id == inspection_id).first()

    @staticmethod
    def delete_inspection(inspection_id: str, db: Optional[Session] = None) -> Optional[Any]:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            doc = col.find_one({"id": inspection_id})
            if not doc:
                return None
            col.delete_one({"id": inspection_id})
            return MongoInspectionRecord(doc)
        else:
            item = db.query(Inspection).filter(Inspection.id == inspection_id).first()
            if not item:
                return None
            db.delete(item)
            db.commit()
            return item

    @staticmethod
    def get_paginated_inspections(
        search: Optional[str] = None,
        status: Optional[str] = None,
        defect_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        db: Optional[Session] = None,
    ) -> Tuple[List[Any], int]:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            filter_query: Dict[str, Any] = {}

            if search:
                regex = {"$regex": search.strip(), "$options": "i"}
                filter_query["$or"] = [
                    {"original_filename": regex},
                    {"product_id": regex},
                    {"inspection_notes": regex}
                ]

            if status and status.upper() in {"ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"}:
                filter_query["status"] = status.upper()

            if defect_type and defect_type != "ALL":
                filter_query["defect_type"] = defect_type

            date_filter = {}
            if date_from:
                try:
                    d_from = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
                    date_filter["$gte"] = d_from
                except ValueError:
                    pass
            if date_to:
                try:
                    d_to = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                    date_filter["$lte"] = d_to
                except ValueError:
                    pass
            if date_filter:
                filter_query["created_at"] = date_filter

            total = col.count_documents(filter_query)
            cursor = col.find(filter_query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
            items = [MongoInspectionRecord(d) for d in cursor]
            return items, total
        else:
            query = db.query(Inspection)
            if search:
                search_filter = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Inspection.original_filename.ilike(search_filter),
                        Inspection.product_id.ilike(search_filter),
                        Inspection.inspection_notes.ilike(search_filter)
                    )
                )
            if status and status.upper() in {"ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"}:
                query = query.filter(Inspection.status == status.upper())
            if defect_type and defect_type != "ALL":
                query = query.filter(Inspection.defect_type == defect_type)
            if date_from:
                try:
                    d_from = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
                    query = query.filter(Inspection.created_at >= d_from)
                except ValueError:
                    pass
            if date_to:
                try:
                    d_to = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                    query = query.filter(Inspection.created_at <= d_to)
                except ValueError:
                    pass
            query = query.order_by(desc(Inspection.created_at))
            total = query.count()
            items = query.offset((page - 1) * page_size).limit(page_size).all()
            return items, total

    @staticmethod
    def get_all_for_csv(
        search: Optional[str] = None,
        status: Optional[str] = None,
        defect_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Any]:
        if is_mongo_enabled():
            col = get_mongo_inspections_collection()
            filter_query: Dict[str, Any] = {}
            if search:
                regex = {"$regex": search.strip(), "$options": "i"}
                filter_query["$or"] = [
                    {"original_filename": regex},
                    {"product_id": regex},
                    {"inspection_notes": regex}
                ]
            if status and status.upper() in {"ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"}:
                filter_query["status"] = status.upper()
            if defect_type and defect_type != "ALL":
                filter_query["defect_type"] = defect_type
            date_filter = {}
            if date_from:
                try:
                    date_filter["$gte"] = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_filter["$lte"] = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                except ValueError:
                    pass
            if date_filter:
                filter_query["created_at"] = date_filter

            cursor = col.find(filter_query).sort("created_at", -1)
            return [MongoInspectionRecord(d) for d in cursor]
        else:
            query = db.query(Inspection)
            if search:
                search_filter = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Inspection.original_filename.ilike(search_filter),
                        Inspection.product_id.ilike(search_filter),
                        Inspection.inspection_notes.ilike(search_filter)
                    )
                )
            if status and status.upper() in {"ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"}:
                query = query.filter(Inspection.status == status.upper())
            if defect_type and defect_type != "ALL":
                query = query.filter(Inspection.defect_type == defect_type)
            if date_from:
                try:
                    query = query.filter(Inspection.created_at >= datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc))
                except ValueError:
                    pass
            if date_to:
                try:
                    query = query.filter(Inspection.created_at <= datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc))
                except ValueError:
                    pass
            return query.order_by(desc(Inspection.created_at)).all()

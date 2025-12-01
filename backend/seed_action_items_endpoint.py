"""
Add this endpoint to server.py to seed action items via API
You can call: POST /api/cockpit/action-items/seed
"""
from datetime import datetime, timezone

@api_router.post("/cockpit/action-items/seed")
async def seed_action_items_endpoint(email: str = Depends(get_current_user)):
    """Seed action items in MongoDB (admin only)"""
    try:
        # Check if data already exists
        existing = await db.cockpit_action_items.find_one({})
        if existing:
            return {
                "message": "Action items already exist",
                "critical_count": len(existing.get('critical', [])),
                "impact_count": len(existing.get('impact', []))
            }
        
        # Action items data
        action_items_data = {
            "critical": [
                {
                    "id": 1,
                    "title": "Reverse 45% YoY Revenue Decline: Emergency Recovery Plan",
                    "dueDate": "2025-12-15",
                    "priority": "high",
                    "impact": "high",
                    "category": "critical",
                    "description": "Urgent action required to address significant year-over-year revenue decline"
                },
                {
                    "id": 2,
                    "title": "Reduce Grocery Channel Concentration from 73.4%",
                    "dueDate": "2025-01-20",
                    "priority": "high",
                    "impact": "high",
                    "category": "critical",
                    "description": "Diversify channel mix to reduce dependency on grocery channel"
                },
                {
                    "id": 3,
                    "title": "Stabilize Top 5 Customer Relationships",
                    "dueDate": "2025-01-15",
                    "priority": "medium",
                    "impact": "high",
                    "category": "critical",
                    "description": "Focus on maintaining and strengthening relationships with top customers"
                },
                {
                    "id": 4,
                    "title": "Audit Food Business Unit Margin Compression",
                    "dueDate": "2025-02-01",
                    "priority": "medium",
                    "impact": "medium",
                    "category": "critical",
                    "description": "Investigate and address margin compression in food business unit"
                },
                {
                    "id": 5,
                    "title": "Launch Online Channel Growth Initiative",
                    "dueDate": "2025-02-28",
                    "priority": "low",
                    "impact": "medium",
                    "category": "critical",
                    "description": "Develop and execute strategy to grow online channel presence"
                }
            ],
            "impact": [
                {
                    "id": 6,
                    "title": "Scale Food Business to €22M+ via Category Expansion",
                    "dueDate": "2025-03-15",
                    "priority": "high",
                    "impact": "high",
                    "category": "impact",
                    "description": "Expand food business categories to achieve revenue target of €22M+"
                },
                {
                    "id": 7,
                    "title": "Develop Wholesale Channel Acceleration Program",
                    "dueDate": "2025-02-28",
                    "priority": "high",
                    "impact": "high",
                    "category": "impact",
                    "description": "Create program to accelerate growth in wholesale channel"
                },
                {
                    "id": 8,
                    "title": "Optimize Household & Beauty Segment Efficiency",
                    "dueDate": "2025-03-20",
                    "priority": "medium",
                    "impact": "medium",
                    "category": "impact",
                    "description": "Improve operational efficiency in household and beauty segments"
                },
                {
                    "id": 9,
                    "title": "Build International Channel to 5% of Revenue Mix",
                    "dueDate": "2025-03-31",
                    "priority": "low",
                    "impact": "medium",
                    "category": "impact",
                    "description": "Develop international channel to reach 5% of total revenue"
                }
            ],
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert into MongoDB
        result = await db.cockpit_action_items.update_one(
            {},
            {"$set": action_items_data},
            upsert=True
        )
        
        logger.info(f"✅ Seeded action items: {len(action_items_data['critical'])} critical, {len(action_items_data['impact'])} impact")
        
        return {
            "message": "Action items seeded successfully",
            "critical_count": len(action_items_data['critical']),
            "impact_count": len(action_items_data['impact'])
        }
        
    except Exception as e:
        logger.error(f"❌ Error seeding action items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error seeding action items: {str(e)}")


"""
Nutrition and Calorie Logger router for FemCare AI.
Provides food database, calorie logging, and AI photo analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, timedelta
from typing import List, Optional
import json
import os
import base64
import httpx

from app.database import get_db
from app import models
from app.security import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/nutrition", tags=["Nutrition & Calories"])


def load_foods_from_json():
    """Load foods from JSON file."""
    # Get the path relative to backend directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(base_dir, "data", "foods.json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Try alternate path
    alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "foods.json")
    if os.path.exists(alt_path):
        with open(alt_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print(f"Warning: foods.json not found at {json_path}")
    return []


def seed_foods(db: Session):
    """Seed foods from JSON if database is empty."""
    existing_count = db.query(models.FoodItem).filter(models.FoodItem.is_custom == False).count()
    if existing_count == 0:
        foods_data = load_foods_from_json()
        for food_data in foods_data:
            food = models.FoodItem(**food_data, is_custom=False)
            db.add(food)
        db.commit()
        print(f"✅ Seeded {len(foods_data)} food items")


def get_current_cycle_phase(user_id: int, db: Session) -> str:
    """Get the current cycle phase for a user."""
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == user_id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if not latest_cycle:
        return "follicular"
    
    today = date.today()
    days_since_start = (today - latest_cycle.start_date).days
    
    if days_since_start <= 5:
        return "menstrual"
    elif days_since_start <= 13:
        return "follicular"
    elif days_since_start <= 16:
        return "ovulation"
    else:
        return "luteal"


@router.get("/foods")
async def get_foods(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get food items with optional filters.
    """
    seed_foods(db)
    
    query = db.query(models.FoodItem).filter(
        (models.FoodItem.is_custom == False) | 
        (models.FoodItem.user_id == current_user.id)
    )
    
    if category:
        query = query.filter(models.FoodItem.category == category)
    
    if search:
        query = query.filter(models.FoodItem.name.ilike(f"%{search}%"))
    
    foods = query.offset(skip).limit(limit).all()
    
    return {
        "foods": [{
            "id": food.id,
            "name": food.name,
            "category": food.category,
            "calories_per_100g": food.calories_per_100g,
            "protein_g": food.protein_g,
            "carbs_g": food.carbs_g,
            "fat_g": food.fat_g,
            "fiber_g": food.fiber_g,
            "serving_size_g": food.serving_size_g,
            "serving_description": food.serving_description,
            "period_phase_benefit": food.period_phase_benefit or {},
            "is_custom": food.is_custom
        } for food in foods],
        "total": len(foods),
        "categories": ["fruits", "vegetables", "proteins", "grains", "dairy", "nuts_seeds", "snacks", "beverages", "fats", "sweeteners", "indian"]
    }


@router.get("/foods/suggestions")
async def get_food_suggestions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get food suggestions based on current cycle phase.
    """
    seed_foods(db)
    
    current_phase = get_current_cycle_phase(current_user.id, db)
    
    # Get foods with benefits for current phase
    all_foods = db.query(models.FoodItem).filter(
        models.FoodItem.is_custom == False
    ).all()
    
    suggested_foods = []
    for food in all_foods:
        benefits = food.period_phase_benefit or {}
        if current_phase in benefits:
            suggested_foods.append({
                "id": food.id,
                "name": food.name,
                "category": food.category,
                "calories_per_100g": food.calories_per_100g,
                "benefit": benefits[current_phase],
                "serving_description": food.serving_description
            })
    
    phase_tips = {
        "menstrual": "Focus on iron-rich foods like spinach, lentils, and red meat. Stay hydrated and include anti-inflammatory foods.",
        "follicular": "Eat light, fresh foods. Include fermented foods and lean proteins to support rising energy.",
        "ovulation": "Support hormone production with healthy fats, fiber-rich vegetables, and antioxidant-rich foods.",
        "luteal": "Combat cravings with complex carbs. Include magnesium-rich foods like dark chocolate and nuts."
    }
    
    return {
        "current_phase": current_phase,
        "phase_tip": phase_tips.get(current_phase, ""),
        "suggestions": suggested_foods,
        "total": len(suggested_foods)
    }


@router.post("/foods/custom")
async def create_custom_food(
    name: str,
    category: str,
    calories_per_100g: float,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    fiber_g: float = 0,
    serving_size_g: float = 100,
    serving_description: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a custom food item.
    """
    food = models.FoodItem(
        name=name,
        category=category,
        calories_per_100g=calories_per_100g,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        fiber_g=fiber_g,
        serving_size_g=serving_size_g,
        serving_description=serving_description,
        is_custom=True,
        user_id=current_user.id
    )
    
    db.add(food)
    db.commit()
    db.refresh(food)
    
    return {
        "id": food.id,
        "name": food.name,
        "message": f"Custom food '{name}' added successfully"
    }


@router.post("/log")
async def log_food(
    food_name: str,
    quantity_grams: float,
    meal_type: str = Query(..., regex="^(breakfast|lunch|dinner|snack)$"),
    food_item_id: Optional[int] = None,
    calories_per_100g: Optional[float] = None,
    protein_per_100g: Optional[float] = None,
    carbs_per_100g: Optional[float] = None,
    fat_per_100g: Optional[float] = None,
    notes: Optional[str] = None,
    log_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a food item with calories.
    """
    # Get nutritional info
    if food_item_id:
        food = db.query(models.FoodItem).filter(models.FoodItem.id == food_item_id).first()
        if food:
            calories_per_100g = food.calories_per_100g
            protein_per_100g = food.protein_g
            carbs_per_100g = food.carbs_g
            fat_per_100g = food.fat_g
    
    # Calculate totals
    multiplier = quantity_grams / 100
    total_calories = (calories_per_100g or 0) * multiplier
    total_protein = (protein_per_100g or 0) * multiplier
    total_carbs = (carbs_per_100g or 0) * multiplier
    total_fat = (fat_per_100g or 0) * multiplier
    
    # Create log entry
    calorie_log = models.CalorieLog(
        user_id=current_user.id,
        food_item_id=food_item_id,
        food_name=food_name,
        date=log_date or date.today(),
        quantity_grams=quantity_grams,
        meal_type=meal_type,
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        notes=notes
    )
    
    db.add(calorie_log)
    db.commit()
    db.refresh(calorie_log)
    
    return {
        "id": calorie_log.id,
        "food_name": calorie_log.food_name,
        "quantity_grams": calorie_log.quantity_grams,
        "meal_type": calorie_log.meal_type,
        "total_calories": round(total_calories, 1),
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "date": str(calorie_log.date),
        "message": f"Logged {quantity_grams}g of {food_name} ({round(total_calories, 0)} kcal)"
    }


@router.get("/logs")
async def get_calorie_logs(
    log_date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    meal_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calorie logs for the current user.
    """
    query = db.query(models.CalorieLog).filter(
        models.CalorieLog.user_id == current_user.id
    )
    
    if log_date:
        query = query.filter(models.CalorieLog.date == log_date)
    if start_date:
        query = query.filter(models.CalorieLog.date >= start_date)
    if end_date:
        query = query.filter(models.CalorieLog.date <= end_date)
    if meal_type:
        query = query.filter(models.CalorieLog.meal_type == meal_type)
    
    logs = query.order_by(desc(models.CalorieLog.date), models.CalorieLog.meal_type).offset(skip).limit(limit).all()
    
    return {
        "logs": [{
            "id": log.id,
            "food_name": log.food_name,
            "date": str(log.date),
            "quantity_grams": log.quantity_grams,
            "meal_type": log.meal_type,
            "total_calories": log.total_calories,
            "total_protein": log.total_protein,
            "total_carbs": log.total_carbs,
            "total_fat": log.total_fat,
            "notes": log.notes
        } for log in logs],
        "total": len(logs)
    }


@router.get("/daily-summary")
async def get_daily_summary(
    summary_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get daily calorie and nutrition summary.
    """
    target_date = summary_date or date.today()
    
    logs = db.query(models.CalorieLog).filter(
        models.CalorieLog.user_id == current_user.id,
        models.CalorieLog.date == target_date
    ).all()
    
    # Calculate totals
    total_calories = sum(log.total_calories for log in logs)
    total_protein = sum(log.total_protein or 0 for log in logs)
    total_carbs = sum(log.total_carbs or 0 for log in logs)
    total_fat = sum(log.total_fat or 0 for log in logs)
    
    # Group by meal type
    meals = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    meal_totals = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    
    for log in logs:
        if log.meal_type in meals:
            meals[log.meal_type].append({
                "id": log.id,
                "food_name": log.food_name,
                "quantity_grams": log.quantity_grams,
                "calories": log.total_calories
            })
            meal_totals[log.meal_type] += log.total_calories
    
    # Default calorie goal (can be customized per user later)
    calorie_goal = 2000
    
    return {
        "date": str(target_date),
        "total_calories": round(total_calories, 0),
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "calorie_goal": calorie_goal,
        "calories_remaining": round(calorie_goal - total_calories, 0),
        "progress_percentage": round((total_calories / calorie_goal) * 100, 1),
        "meals": meals,
        "meal_totals": {k: round(v, 0) for k, v in meal_totals.items()},
        "total_items_logged": len(logs)
    }


@router.post("/analyze-photo")
async def analyze_food_photo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a food photo using AI (Ollama with vision model) to detect food items and estimate calories.
    """
    # Read and encode image
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode('utf-8')
    
    # Save photo
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    photo_filename = f"{current_user.id}_{date.today().isoformat()}_{file.filename}"
    photo_path = os.path.join(upload_dir, photo_filename)
    
    with open(photo_path, 'wb') as f:
        f.write(contents)
    
    # Try to analyze with Ollama vision model
    detected_foods = []
    estimated_calories = 0
    confidence = 0.0
    analysis_result = {}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Use llava model for vision
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": "llava",
                    "prompt": """Analyze this food image. Identify each food item visible and estimate:
1. The food name
2. Estimated portion size in grams
3. Estimated calories

Respond in this exact JSON format:
{
    "foods": [
        {"name": "food name", "portion_grams": 100, "calories": 150},
        ...
    ],
    "total_estimated_calories": 500,
    "confidence": 0.8
}

Only include the JSON, no other text.""",
                    "images": [base64_image],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Try to parse JSON from response
                try:
                    # Find JSON in response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        analysis_result = json.loads(json_match.group())
                        detected_foods = analysis_result.get("foods", [])
                        estimated_calories = analysis_result.get("total_estimated_calories", 0)
                        confidence = analysis_result.get("confidence", 0.7)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract info manually
                    detected_foods = [{"name": "Unknown food", "portion_grams": 100, "calories": 200}]
                    estimated_calories = 200
                    confidence = 0.3
                    
    except Exception as e:
        # Fallback if Ollama is not available
        print(f"AI analysis failed: {e}")
        detected_foods = [{"name": "Food item (AI unavailable)", "portion_grams": 100, "calories": 200}]
        estimated_calories = 200
        confidence = 0.1
        analysis_result = {"error": str(e), "message": "AI analysis unavailable, using default estimate"}
    
    # Save analysis to database
    food_analysis = models.FoodAnalysis(
        user_id=current_user.id,
        photo_path=photo_path,
        analysis_result=analysis_result,
        detected_foods=detected_foods,
        estimated_calories=estimated_calories,
        confidence_score=confidence
    )
    
    db.add(food_analysis)
    db.commit()
    db.refresh(food_analysis)
    
    return {
        "analysis_id": food_analysis.id,
        "detected_foods": detected_foods,
        "estimated_calories": estimated_calories,
        "confidence": confidence,
        "photo_saved": True,
        "message": "Photo analyzed successfully" if confidence > 0.5 else "Analysis completed with low confidence"
    }


@router.post("/analyze-photo/{analysis_id}/log")
async def log_analyzed_foods(
    analysis_id: int,
    meal_type: str = Query(..., regex="^(breakfast|lunch|dinner|snack)$"),
    log_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log foods from a photo analysis.
    """
    analysis = db.query(models.FoodAnalysis).filter(
        models.FoodAnalysis.id == analysis_id,
        models.FoodAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    logged_items = []
    total_calories = 0
    
    for food in analysis.detected_foods or []:
        food_name = food.get("name", "Unknown")
        quantity = food.get("portion_grams", 100)
        calories = food.get("calories", 0)
        
        calorie_log = models.CalorieLog(
            user_id=current_user.id,
            food_name=food_name,
            date=log_date or date.today(),
            quantity_grams=quantity,
            meal_type=meal_type,
            total_calories=calories,
            photo_path=analysis.photo_path
        )
        
        db.add(calorie_log)
        logged_items.append(food_name)
        total_calories += calories
    
    analysis.is_logged = True
    db.commit()
    
    return {
        "logged_items": logged_items,
        "total_calories": total_calories,
        "meal_type": meal_type,
        "message": f"Logged {len(logged_items)} items totaling {round(total_calories, 0)} calories"
    }


@router.get("/stats")
async def get_nutrition_stats(
    days: int = Query(30, ge=7, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nutrition statistics for the current user.
    """
    start_date = date.today() - timedelta(days=days)
    
    logs = db.query(models.CalorieLog).filter(
        models.CalorieLog.user_id == current_user.id,
        models.CalorieLog.date >= start_date
    ).all()
    
    if not logs:
        return {
            "days_tracked": 0,
            "total_calories": 0,
            "avg_daily_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fat": 0,
            "favorite_foods": [],
            "calories_by_meal": {}
        }
    
    total_calories = sum(log.total_calories for log in logs)
    total_protein = sum(log.total_protein or 0 for log in logs)
    total_carbs = sum(log.total_carbs or 0 for log in logs)
    total_fat = sum(log.total_fat or 0 for log in logs)
    
    # Count unique days
    unique_days = len(set(log.date for log in logs))
    
    # Count foods
    food_counts = {}
    meal_calories = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    
    for log in logs:
        food_counts[log.food_name] = food_counts.get(log.food_name, 0) + 1
        if log.meal_type in meal_calories:
            meal_calories[log.meal_type] += log.total_calories
    
    favorite_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "days_tracked": unique_days,
        "total_calories": round(total_calories, 0),
        "avg_daily_calories": round(total_calories / unique_days, 0) if unique_days > 0 else 0,
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "favorite_foods": [{"name": name, "count": count} for name, count in favorite_foods],
        "calories_by_meal": {k: round(v, 0) for k, v in meal_calories.items()},
        "total_items_logged": len(logs)
    }


@router.delete("/logs/{log_id}")
async def delete_calorie_log(
    log_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a calorie log entry.
    """
    log = db.query(models.CalorieLog).filter(
        models.CalorieLog.id == log_id,
        models.CalorieLog.user_id == current_user.id
    ).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    db.delete(log)
    db.commit()
    
    return {"message": "Log entry deleted successfully"}


# ============== AI Photo Analysis ==============

async def analyze_with_ollama(image_base64: str) -> dict:
    """Analyze food image using local Ollama with LLaVA."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": "llava",
                    "prompt": """Analyze this food image. Identify the food items and estimate calories.
                    Return ONLY a JSON object in this exact format:
                    {
                        "foods": [
                            {"name": "food name", "portion": "estimated portion", "calories": estimated_calories}
                        ],
                        "total_calories": total,
                        "confidence": 0.0-1.0
                    }""",
                    "images": [image_base64],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parse the response
                import re
                text = result.get("response", "")
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return {"success": True, "data": json.loads(json_match.group()), "source": "ollama"}
            
            return {"success": False, "error": "Ollama response parsing failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def analyze_with_imagga(image_base64: str) -> dict:
    """Analyze food image using Imagga API."""
    if not settings.IMAGGA_API_KEY or not settings.IMAGGA_API_SECRET:
        return {"success": False, "error": "Imagga API not configured"}
    
    try:
        import base64
        import requests
        import asyncio
        
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        
        # Comprehensive food calorie database (per 100g)
        food_database = {
            # Fruits
            "apple": (52, 182), "banana": (89, 118), "orange": (47, 131),
            "grapes": (67, 150), "mango": (60, 200), "strawberry": (32, 150),
            "watermelon": (30, 280), "papaya": (43, 150), "pineapple": (50, 166),
            "pomegranate": (83, 174), "guava": (68, 165), "kiwi": (61, 76),
            "fruit": (50, 150),
            
            # Vegetables  
            "vegetables": (35, 100), "salad": (20, 200), "tomato": (18, 123),
            "potato": (77, 150), "carrot": (41, 61), "cucumber": (16, 100),
            "spinach": (23, 100), "broccoli": (34, 100), "cauliflower": (25, 100),
            "vegetable": (35, 100),
            
            # Grains & Carbs
            "rice": (130, 200), "bread": (265, 30), "roti": (300, 25),
            "pasta": (131, 150), "noodles": (138, 200), "chapati": (240, 30),
            "paratha": (260, 100), "dosa": (120, 140), "idli": (39, 60),
            "poha": (158, 200), "upma": (100, 200),
            
            # Protein
            "chicken": (165, 150), "fish": (140, 150), "egg": (155, 50),
            "beef": (250, 150), "mutton": (234, 150), "paneer": (265, 100),
            "tofu": (76, 100), "dal": (116, 200), "rajma": (127, 200),
            "chickpea": (164, 150), "chana": (164, 150), "meat": (200, 150),
            
            # Dairy
            "milk": (42, 250), "cheese": (402, 30), "yogurt": (59, 150),
            "curd": (60, 150), "butter": (717, 10), "ghee": (900, 10),
            
            # Fast Food
            "pizza": (266, 107), "burger": (295, 120), "sandwich": (250, 150),
            "french fries": (312, 100), "samosa": (262, 80), "pakora": (250, 60),
            "biryani": (143, 350), "pulao": (140, 300), "curry": (120, 200),
            "food": (150, 200), "meal": (180, 250), "dish": (160, 200),
            
            # Beverages
            "coffee": (2, 250), "tea": (1, 200), "juice": (45, 250),
            "soda": (41, 350), "lassi": (72, 250), "milkshake": (113, 300),
            
            # Desserts
            "cake": (350, 100), "cookie": (500, 30), "ice cream": (207, 100),
            "chocolate": (546, 40), "gulab jamun": (320, 50), "jalebi": (350, 50),
            "kheer": (120, 150), "halwa": (220, 100), "sweet": (300, 80)
        }
        
        def sync_imagga_call():
            """Synchronous Imagga API call using requests library."""
            auth = (settings.IMAGGA_API_KEY, settings.IMAGGA_API_SECRET)
            
            # Upload the image
            print("[Imagga] Uploading image...")
            upload_response = requests.post(
                "https://api.imagga.com/v2/uploads",
                auth=auth,
                files={"image": ("food.jpg", image_data, "image/jpeg")},
                timeout=60
            )
            
            print(f"[Imagga] Upload status: {upload_response.status_code}")
            
            if upload_response.status_code != 200:
                return {"success": False, "error": f"Upload failed: {upload_response.status_code} - {upload_response.text[:200]}"}
            
            upload_data = upload_response.json()
            upload_id = upload_data.get("result", {}).get("upload_id")
            
            if not upload_id:
                return {"success": False, "error": "No upload_id received"}
            
            print(f"[Imagga] Upload ID: {upload_id}")
            
            # Get tags
            tags_response = requests.get(
                f"https://api.imagga.com/v2/tags?image_upload_id={upload_id}",
                auth=auth,
                timeout=60
            )
            
            print(f"[Imagga] Tags status: {tags_response.status_code}")
            
            if tags_response.status_code != 200:
                return {"success": False, "error": f"Tags failed: {tags_response.status_code}"}
            
            tags_data = tags_response.json()
            tags = tags_data.get("result", {}).get("tags", [])
            
            print(f"[Imagga] Found {len(tags)} tags")
            if tags:
                top_5 = [t.get("tag", {}).get("en", "") for t in tags[:5]]
                print(f"[Imagga] Top tags: {top_5}")
            
            return {"success": True, "tags": tags}
        
        # Run synchronous call in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_imagga_call)
        
        if not result.get("success"):
            return result
        
        tags = result.get("tags", [])
        
        # Process tags and match with food database
        foods = []
        total_cal = 0
        
        for tag in tags[:10]:
            tag_name = tag.get("tag", {}).get("en", "").lower()
            confidence = tag.get("confidence", 0)
            
            if confidence < 5:
                continue
            
            for food, (cal_per_100g, serving_g) in food_database.items():
                if food in tag_name or tag_name in food:
                    calories = round((cal_per_100g * serving_g) / 100)
                    foods.append({
                        "name": tag_name.title(),
                        "portion": f"1 serving ({serving_g}g)",
                        "calories": calories,
                        "calories_per_100g": cal_per_100g,
                        "serving_grams": serving_g,
                        "confidence": round(confidence, 1)
                    })
                    total_cal += calories
                    break
        
        if foods:
            return {
                "success": True,
                "data": {
                    "foods": foods,
                    "total_calories": total_cal,
                    "confidence": 0.7
                },
                "source": "imagga"
            }
        else:
            # Return top tag as estimate
            if tags:
                top_tag = tags[0].get("tag", {}).get("en", "Food item")
                return {
                    "success": True,
                    "data": {
                        "foods": [{
                            "name": top_tag.title(),
                            "portion": "1 serving (estimated)",
                            "calories": 150,
                            "confidence": tags[0].get("confidence", 50)
                        }],
                        "total_calories": 150,
                        "confidence": 0.5,
                        "note": "Generic estimate - please adjust calories manually"
                    },
                    "source": "imagga"
                }
            return {"success": False, "error": "No food items detected in image"}
    
    except Exception as e:
        print(f"[Imagga] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/analyze-photo")
async def analyze_food_photo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a food photo using AI to identify foods and estimate calories.
    Tries Imagga API first (if configured), falls back to Ollama.
    """
    # Read and encode the image
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")
    
    print(f"[Photo Analysis] Received image, size: {len(contents)} bytes")
    
    # Try Imagga first if configured (more reliable)
    result = None
    if settings.IMAGGA_API_KEY and settings.IMAGGA_API_SECRET:
        print("[Photo Analysis] Trying Imagga API...")
        result = await analyze_with_imagga(image_base64)
        if result.get("success"):
            print("[Photo Analysis] Imagga succeeded!")
    
    # Fall back to Ollama if Imagga failed or not configured
    if not result or not result.get("success"):
        print("[Photo Analysis] Trying Ollama...")
        ollama_result = await analyze_with_ollama(image_base64)
        if ollama_result.get("success"):
            result = ollama_result
            print("[Photo Analysis] Ollama succeeded!")
        elif not result:
            result = ollama_result
    
    if not result.get("success"):
        print(f"[Photo Analysis] All attempts failed: {result.get('error')}")
        # Return helpful message if both fail
        return {
            "success": False,
            "message": "AI analysis unavailable. Please log food manually.",
            "error": result.get("error", "No AI service available"),
            "manual_entry_required": True,
            "suggestions": [
                {"name": "Rice", "portion": "1 cup", "calories": 206},
                {"name": "Dal", "portion": "1 cup", "calories": 116},
                {"name": "Roti", "portion": "1 piece", "calories": 70},
                {"name": "Salad", "portion": "1 bowl", "calories": 150},
                {"name": "Chicken Curry", "portion": "1 cup", "calories": 243}
            ]
        }
    
    return {
        "success": True,
        "data": result.get("data"),
        "source": result.get("source"),
        "message": f"Analysis completed using {result.get('source', 'AI')}"
    }


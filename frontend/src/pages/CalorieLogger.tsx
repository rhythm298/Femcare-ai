/**
 * Calorie Logger Page - Food tracking and AI photo analysis
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Apple,
    Search,
    Camera,
    Plus,
    Flame,
    TrendingUp,
    Clock,
    Trash2,
    X,
    Check,
    ChevronDown,
    Upload
} from 'lucide-react';
import './CalorieLogger.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const nutritionApi = {
    getFoods: async (params?: { category?: string; search?: string }) => {
        const searchParams = new URLSearchParams();
        if (params?.category) searchParams.set('category', params.category);
        if (params?.search) searchParams.set('search', params.search);
        const response = await fetch(`${API_BASE_URL}/nutrition/foods?${searchParams}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch foods');
        return response.json();
    },
    getFoodSuggestions: async () => {
        const response = await fetch(`${API_BASE_URL}/nutrition/foods/suggestions`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch suggestions');
        return response.json();
    },
    logFood: async (data: {
        food_name: string;
        quantity_grams: number;
        meal_type: string;
        food_item_id?: number;
        calories_per_100g?: number;
        protein_per_100g?: number;
        carbs_per_100g?: number;
        fat_per_100g?: number;
        notes?: string;
    }) => {
        const params = new URLSearchParams();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined) params.set(key, String(value));
        });
        const response = await fetch(`${API_BASE_URL}/nutrition/log?${params}`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to log food');
        return response.json();
    },
    getDailySummary: async (date?: string) => {
        const params = date ? `?summary_date=${date}` : '';
        const response = await fetch(`${API_BASE_URL}/nutrition/daily-summary${params}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch summary');
        return response.json();
    },
    analyzePhoto: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        const token = localStorage.getItem('femcare_token');
        const response = await fetch(`${API_BASE_URL}/nutrition/analyze-photo`, {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: formData
        });
        if (!response.ok) throw new Error('Failed to analyze photo');
        return response.json();
    },
    logAnalyzedFoods: async (analysisId: number, mealType: string) => {
        const response = await fetch(
            `${API_BASE_URL}/nutrition/analyze-photo/${analysisId}/log?meal_type=${mealType}`,
            { method: 'POST', headers: getAuthHeader() }
        );
        if (!response.ok) throw new Error('Failed to log analyzed foods');
        return response.json();
    },
    deleteLog: async (logId: number) => {
        const response = await fetch(`${API_BASE_URL}/nutrition/logs/${logId}`, {
            method: 'DELETE',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to delete log');
        return response.json();
    },
    createCustomFood: async (data: {
        name: string;
        category: string;
        calories_per_100g: number;
        protein_g?: number;
        carbs_g?: number;
        fat_g?: number;
    }) => {
        const params = new URLSearchParams();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined) params.set(key, String(value));
        });
        const response = await fetch(`${API_BASE_URL}/nutrition/foods/custom?${params}`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to create custom food');
        return response.json();
    }
};

interface FoodItem {
    id: number;
    name: string;
    category: string;
    calories_per_100g: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    serving_size_g: number;
    serving_description: string;
    period_phase_benefit: Record<string, string>;
    is_custom: boolean;
}

const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'] as const;

const mealIcons: Record<string, string> = {
    breakfast: '🌅',
    lunch: '☀️',
    dinner: '🌙',
    snack: '🍎'
};

export default function CalorieLogger() {
    const queryClient = useQueryClient();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [selectedMeal, setSelectedMeal] = useState<typeof mealTypes[number]>('breakfast');
    const [showLogModal, setShowLogModal] = useState(false);
    const [showPhotoModal, setShowPhotoModal] = useState(false);
    const [showCustomFoodModal, setShowCustomFoodModal] = useState(false);
    const [selectedFood, setSelectedFood] = useState<FoodItem | null>(null);
    const [logQuantity, setLogQuantity] = useState(100);
    const [logNotes, setLogNotes] = useState('');
    const [photoFile, setPhotoFile] = useState<File | null>(null);
    const [photoPreview, setPhotoPreview] = useState<string | null>(null);
    const [photoAnalysis, setPhotoAnalysis] = useState<any>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // Custom food form
    const [customFood, setCustomFood] = useState({
        name: '',
        category: 'snacks',
        calories_per_100g: 0,
        protein_g: 0,
        carbs_g: 0,
        fat_g: 0
    });

    const { data: foods, isLoading: foodsLoading } = useQuery({
        queryKey: ['foods', selectedCategory, searchQuery],
        queryFn: () => nutritionApi.getFoods({ category: selectedCategory || undefined, search: searchQuery || undefined })
    });

    const { data: suggestions } = useQuery({
        queryKey: ['foodSuggestions'],
        queryFn: nutritionApi.getFoodSuggestions
    });

    const { data: dailySummary, isLoading: summaryLoading } = useQuery({
        queryKey: ['dailySummary'],
        queryFn: () => nutritionApi.getDailySummary()
    });

    const logMutation = useMutation({
        mutationFn: nutritionApi.logFood,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['dailySummary'] });
            setShowLogModal(false);
            setSelectedFood(null);
            setLogQuantity(100);
            setLogNotes('');
        }
    });

    const deleteMutation = useMutation({
        mutationFn: nutritionApi.deleteLog,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['dailySummary'] });
        }
    });

    const customFoodMutation = useMutation({
        mutationFn: nutritionApi.createCustomFood,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['foods'] });
            setShowCustomFoodModal(false);
            setCustomFood({
                name: '',
                category: 'snacks',
                calories_per_100g: 0,
                protein_g: 0,
                carbs_g: 0,
                fat_g: 0
            });
        }
    });

    const handleFoodSelect = (food: FoodItem) => {
        setSelectedFood(food);
        setLogQuantity(food.serving_size_g || 100);
        setShowLogModal(true);
    };

    const handleLogFood = () => {
        if (!selectedFood) return;
        logMutation.mutate({
            food_name: selectedFood.name,
            quantity_grams: logQuantity,
            meal_type: selectedMeal,
            food_item_id: selectedFood.id,
            calories_per_100g: selectedFood.calories_per_100g,
            protein_per_100g: selectedFood.protein_g,
            carbs_per_100g: selectedFood.carbs_g,
            fat_per_100g: selectedFood.fat_g,
            notes: logNotes || undefined
        });
    };

    const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setPhotoFile(file);
            setPhotoPreview(URL.createObjectURL(file));
            setPhotoAnalysis(null);
        }
    };

    const handleAnalyzePhoto = async () => {
        if (!photoFile) return;
        setIsAnalyzing(true);
        try {
            const result = await nutritionApi.analyzePhoto(photoFile);
            setPhotoAnalysis(result);
        } catch (error) {
            console.error('Analysis failed:', error);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleLogAnalyzedFoods = async () => {
        if (!photoAnalysis?.analysis_id) return;
        try {
            await nutritionApi.logAnalyzedFoods(photoAnalysis.analysis_id, selectedMeal);
            queryClient.invalidateQueries({ queryKey: ['dailySummary'] });
            setShowPhotoModal(false);
            setPhotoFile(null);
            setPhotoPreview(null);
            setPhotoAnalysis(null);
        } catch (error) {
            console.error('Failed to log analyzed foods:', error);
        }
    };

    const categories = [
        { id: 'fruits', name: 'Fruits', emoji: '🍎' },
        { id: 'vegetables', name: 'Vegetables', emoji: '🥗' },
        { id: 'proteins', name: 'Proteins', emoji: '🍗' },
        { id: 'grains', name: 'Grains', emoji: '🍚' },
        { id: 'dairy', name: 'Dairy', emoji: '🥛' },
        { id: 'indian', name: 'Indian', emoji: '🍛' },
        { id: 'snacks', name: 'Snacks', emoji: '🍪' },
        { id: 'beverages', name: 'Beverages', emoji: '🍵' }
    ];

    const progressPercentage = dailySummary?.progress_percentage || 0;
    const progressColor = progressPercentage > 100 ? 'var(--error)' : progressPercentage > 80 ? 'var(--warning)' : 'var(--success)';

    return (
        <div className="calorie-page animate-fade-in">
            {/* Header */}
            <div className="calorie-header">
                <div>
                    <h1><Apple size={28} /> Calorie Logger</h1>
                    <p className="today-date">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-secondary" onClick={() => setShowPhotoModal(true)}>
                        <Camera size={18} /> Scan Food
                    </button>
                    <button className="btn btn-primary" onClick={() => setShowCustomFoodModal(true)}>
                        <Plus size={18} /> Add Custom
                    </button>
                </div>
            </div>

            {/* Daily Summary */}
            <div className="daily-summary-card">
                <div className="calorie-ring" style={{ '--progress': `${Math.min(progressPercentage, 100)}%`, '--color': progressColor } as React.CSSProperties}>
                    <div className="ring-content">
                        <span className="calories-consumed">{dailySummary?.total_calories || 0}</span>
                        <span className="calories-label">kcal</span>
                    </div>
                </div>
                <div className="summary-details">
                    <div className="summary-row">
                        <span>Daily Goal</span>
                        <strong>{dailySummary?.calorie_goal || 2000} kcal</strong>
                    </div>
                    <div className="summary-row">
                        <span>Remaining</span>
                        <strong style={{ color: dailySummary?.calories_remaining < 0 ? 'var(--error)' : 'var(--success)' }}>
                            {dailySummary?.calories_remaining || 2000} kcal
                        </strong>
                    </div>
                    <div className="macro-bars">
                        <div className="macro-item">
                            <span className="macro-label">Protein</span>
                            <span className="macro-value">{dailySummary?.total_protein?.toFixed(0) || 0}g</span>
                        </div>
                        <div className="macro-item">
                            <span className="macro-label">Carbs</span>
                            <span className="macro-value">{dailySummary?.total_carbs?.toFixed(0) || 0}g</span>
                        </div>
                        <div className="macro-item">
                            <span className="macro-label">Fat</span>
                            <span className="macro-value">{dailySummary?.total_fat?.toFixed(0) || 0}g</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Meal Tabs */}
            <div className="meal-tabs">
                {mealTypes.map(meal => (
                    <button
                        key={meal}
                        className={`meal-tab ${selectedMeal === meal ? 'active' : ''}`}
                        onClick={() => setSelectedMeal(meal)}
                    >
                        <span className="meal-emoji">{mealIcons[meal]}</span>
                        <span className="meal-name">{meal.charAt(0).toUpperCase() + meal.slice(1)}</span>
                        <span className="meal-calories">{dailySummary?.meal_totals?.[meal] || 0}</span>
                    </button>
                ))}
            </div>

            {/* Logged Foods for Selected Meal */}
            {dailySummary?.meals?.[selectedMeal]?.length > 0 && (
                <div className="logged-foods-section">
                    <h3>Logged for {selectedMeal}</h3>
                    <div className="logged-foods-list">
                        {dailySummary.meals[selectedMeal].map((item: any) => (
                            <div key={item.id} className="logged-food-item">
                                <div className="logged-food-info">
                                    <span className="food-name">{item.food_name}</span>
                                    <span className="food-quantity">{item.quantity_grams}g</span>
                                </div>
                                <div className="logged-food-calories">
                                    <Flame size={14} />
                                    {Math.round(item.calories)} kcal
                                </div>
                                <button
                                    className="delete-btn"
                                    onClick={() => deleteMutation.mutate(item.id)}
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Food Suggestions */}
            {suggestions?.suggestions && suggestions.suggestions.length > 0 && (
                <section className="suggestions-section">
                    <h3>Recommended for {suggestions.current_phase} phase</h3>
                    <p className="phase-tip">{suggestions.phase_tip}</p>
                    <div className="suggestion-chips">
                        {suggestions.suggestions.slice(0, 8).map((food: any) => (
                            <div
                                key={food.id}
                                className="suggestion-chip"
                                onClick={() => handleFoodSelect(food)}
                            >
                                <span className="chip-name">{food.name}</span>
                                <span className="chip-benefit">{food.benefit?.substring(0, 30)}...</span>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Search & Browse */}
            <section className="browse-section">
                <div className="search-bar">
                    <Search size={20} />
                    <input
                        type="text"
                        placeholder="Search foods..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="category-pills">
                    <button
                        className={`category-pill ${!selectedCategory ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(null)}
                    >
                        All
                    </button>
                    {categories.map(cat => (
                        <button
                            key={cat.id}
                            className={`category-pill ${selectedCategory === cat.id ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(cat.id)}
                        >
                            {cat.emoji} {cat.name}
                        </button>
                    ))}
                </div>

                <div className="food-grid">
                    {foodsLoading ? (
                        <div className="loading-foods">Loading foods...</div>
                    ) : (
                        foods?.foods?.map((food: FoodItem) => (
                            <div
                                key={food.id}
                                className="food-card"
                                onClick={() => handleFoodSelect(food)}
                            >
                                <div className="food-card-header">
                                    <span className="food-name">{food.name}</span>
                                    {food.is_custom && <span className="custom-badge">Custom</span>}
                                </div>
                                <div className="food-card-nutrition">
                                    <span className="calories">{food.calories_per_100g} kcal</span>
                                    <span className="serving">/100g</span>
                                </div>
                                <div className="food-macros">
                                    <span>P: {food.protein_g}g</span>
                                    <span>C: {food.carbs_g}g</span>
                                    <span>F: {food.fat_g}g</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </section>

            {/* Log Modal */}
            {showLogModal && selectedFood && (
                <div className="modal-overlay" onClick={() => setShowLogModal(false)}>
                    <div className="modal log-food-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Log Food</h3>
                            <button className="close-btn" onClick={() => setShowLogModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="selected-food-preview">
                                <h4>{selectedFood.name}</h4>
                                <p>{selectedFood.calories_per_100g} kcal per 100g</p>
                            </div>

                            <div className="form-group">
                                <label>Meal</label>
                                <div className="meal-select">
                                    {mealTypes.map(meal => (
                                        <button
                                            key={meal}
                                            className={`meal-option ${selectedMeal === meal ? 'active' : ''}`}
                                            onClick={() => setSelectedMeal(meal)}
                                        >
                                            {mealIcons[meal]} {meal}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Quantity (grams)</label>
                                <div className="quantity-input">
                                    <button onClick={() => setLogQuantity(Math.max(10, logQuantity - 25))}>-</button>
                                    <input
                                        type="number"
                                        value={logQuantity}
                                        onChange={e => setLogQuantity(parseInt(e.target.value) || 0)}
                                    />
                                    <button onClick={() => setLogQuantity(logQuantity + 25)}>+</button>
                                </div>
                                {selectedFood.serving_description && (
                                    <p className="serving-hint">1 serving = {selectedFood.serving_size_g}g ({selectedFood.serving_description})</p>
                                )}
                            </div>

                            <div className="calculated-nutrition">
                                <div className="calc-item">
                                    <Flame size={16} />
                                    <span>{Math.round((selectedFood.calories_per_100g * logQuantity) / 100)} kcal</span>
                                </div>
                                <div className="calc-item">
                                    <span>P: {((selectedFood.protein_g * logQuantity) / 100).toFixed(1)}g</span>
                                </div>
                                <div className="calc-item">
                                    <span>C: {((selectedFood.carbs_g * logQuantity) / 100).toFixed(1)}g</span>
                                </div>
                                <div className="calc-item">
                                    <span>F: {((selectedFood.fat_g * logQuantity) / 100).toFixed(1)}g</span>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Notes (optional)</label>
                                <input
                                    type="text"
                                    value={logNotes}
                                    onChange={e => setLogNotes(e.target.value)}
                                    placeholder="Add a note..."
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowLogModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={handleLogFood}
                                disabled={logMutation.isPending}
                            >
                                {logMutation.isPending ? 'Logging...' : 'Log Food'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Photo Analysis Modal */}
            {showPhotoModal && (
                <div className="modal-overlay" onClick={() => setShowPhotoModal(false)}>
                    <div className="modal photo-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Analyze Food Photo</h3>
                            <button className="close-btn" onClick={() => setShowPhotoModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            {!photoPreview ? (
                                <label className="photo-upload-area">
                                    <Upload size={40} />
                                    <span>Click to upload a photo</span>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={handlePhotoSelect}
                                        hidden
                                    />
                                </label>
                            ) : (
                                <div className="photo-preview">
                                    <img src={photoPreview} alt="Food to analyze" />
                                    {!photoAnalysis && (
                                        <button
                                            className="btn btn-primary analyze-btn"
                                            onClick={handleAnalyzePhoto}
                                            disabled={isAnalyzing}
                                        >
                                            {isAnalyzing ? 'Analyzing...' : 'Analyze with AI'}
                                        </button>
                                    )}
                                </div>
                            )}

                            {photoAnalysis && (
                                <div className="analysis-results">
                                    <h4>Detected Foods</h4>
                                    <div className="detected-foods">
                                        {photoAnalysis.detected_foods?.map((food: any, i: number) => (
                                            <div key={i} className="detected-food-item">
                                                <span className="food-name">{food.name}</span>
                                                <span className="food-portion">{food.portion_grams}g</span>
                                                <span className="food-cals">{food.calories} kcal</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="total-estimate">
                                        <strong>Total Estimated: {photoAnalysis.estimated_calories} kcal</strong>
                                        <span className="confidence">Confidence: {(photoAnalysis.confidence * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="form-group">
                                        <label>Log to which meal?</label>
                                        <div className="meal-select">
                                            {mealTypes.map(meal => (
                                                <button
                                                    key={meal}
                                                    className={`meal-option ${selectedMeal === meal ? 'active' : ''}`}
                                                    onClick={() => setSelectedMeal(meal)}
                                                >
                                                    {mealIcons[meal]} {meal}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="modal-footer">
                            <button
                                className="btn btn-secondary"
                                onClick={() => {
                                    setShowPhotoModal(false);
                                    setPhotoFile(null);
                                    setPhotoPreview(null);
                                    setPhotoAnalysis(null);
                                }}
                            >
                                Cancel
                            </button>
                            {photoAnalysis && (
                                <button
                                    className="btn btn-primary"
                                    onClick={handleLogAnalyzedFoods}
                                >
                                    <Check size={18} /> Log These Foods
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Custom Food Modal */}
            {showCustomFoodModal && (
                <div className="modal-overlay" onClick={() => setShowCustomFoodModal(false)}>
                    <div className="modal custom-food-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Add Custom Food</h3>
                            <button className="close-btn" onClick={() => setShowCustomFoodModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Food Name *</label>
                                <input
                                    type="text"
                                    value={customFood.name}
                                    onChange={e => setCustomFood({ ...customFood, name: e.target.value })}
                                    placeholder="e.g., Mom's Special Dal"
                                />
                            </div>
                            <div className="form-group">
                                <label>Category</label>
                                <select
                                    value={customFood.category}
                                    onChange={e => setCustomFood({ ...customFood, category: e.target.value })}
                                >
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Calories per 100g *</label>
                                <input
                                    type="number"
                                    value={customFood.calories_per_100g}
                                    onChange={e => setCustomFood({ ...customFood, calories_per_100g: parseFloat(e.target.value) || 0 })}
                                />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Protein (g)</label>
                                    <input
                                        type="number"
                                        value={customFood.protein_g}
                                        onChange={e => setCustomFood({ ...customFood, protein_g: parseFloat(e.target.value) || 0 })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Carbs (g)</label>
                                    <input
                                        type="number"
                                        value={customFood.carbs_g}
                                        onChange={e => setCustomFood({ ...customFood, carbs_g: parseFloat(e.target.value) || 0 })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Fat (g)</label>
                                    <input
                                        type="number"
                                        value={customFood.fat_g}
                                        onChange={e => setCustomFood({ ...customFood, fat_g: parseFloat(e.target.value) || 0 })}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowCustomFoodModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => customFoodMutation.mutate(customFood)}
                                disabled={!customFood.name || customFoodMutation.isPending}
                            >
                                {customFoodMutation.isPending ? 'Adding...' : 'Add Food'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

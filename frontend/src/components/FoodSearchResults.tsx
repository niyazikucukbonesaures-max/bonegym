import { memo } from 'react'
import type { FoodItem } from '@/lib/api'

interface FoodSearchResultsProps {
  results: FoodItem[]
  selectedFood: FoodItem | null
  onFoodSelect: (food: FoodItem) => void
  isSearching: boolean
  maxResults?: number
}

export const FoodSearchResults = memo(function FoodSearchResults({
  results,
  selectedFood,
  onFoodSelect,
  isSearching,
  maxResults = 8
}: FoodSearchResultsProps) {
  const limitedResults = results.slice(0, maxResults)
  
  if (results.length === 0) return null

  return (
    <div className="space-y-2 max-h-48 overflow-y-auto scroll-container">
      {isSearching && (
        <div className="p-3 text-center text-white/60">
          Aranıyor...
        </div>
      )}
      {limitedResults.map((food) => (
        <div
          key={food.id}
          onClick={() => onFoodSelect(food)}
          className={`p-3 rounded-lg cursor-pointer transition-colors duration-150 ${
            selectedFood?.id === food.id
              ? 'bg-violet-600/30 border border-violet-500'
              : 'bg-white/5 border border-white/10 hover:bg-white/10'
          }`}
        >
          <p className="text-white font-medium truncate">{food.name}</p>
          <p className="text-sm text-white/60">
            {food.calories_per_100g} kcal / 100g
          </p>
        </div>
      ))}
      {results.length > maxResults && (
        <div className="p-2 text-center text-white/40 text-sm">
          {results.length - maxResults} daha fazla sonuç var...
        </div>
      )}
    </div>
  )
})
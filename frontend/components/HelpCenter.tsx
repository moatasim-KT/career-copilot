import React, { useState, useEffect } from 'react'
import { ResponsiveModal } from './ResponsiveModal'
import { Button } from './ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { 
  MagnifyingGlassIcon,
  BookOpenIcon,
  QuestionMarkCircleIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  ChevronRightIcon,
  StarIcon
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/helpers'
import { apiClient } from '@/utils/api'

interface HelpArticle {
  id: number
  title: string
  slug: string
  content?: string
  excerpt?: string
  category: string
  tags: string[]
  view_count: number
  helpful_votes: number
  unhelpful_votes: number
  created_at: string
  updated_at: string
  user_vote?: boolean | null
}

interface HelpCenterProps {
  isOpen: boolean
  onClose: () => void
  initialQuery?: string
  initialCategory?: string
}

export function HelpCenter({
  isOpen,
  onClose,
  initialQuery = '',
  initialCategory
}: HelpCenterProps) {
  const [view, setView] = useState<'home' | 'search' | 'article' | 'category'>('home')
  const [searchQuery, setSearchQuery] = useState(initialQuery)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(initialCategory || null)
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null)
  const [articles, setArticles] = useState<HelpArticle[]>([])
  const [popularArticles, setPopularArticles] = useState<HelpArticle[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<{
    articles: HelpArticle[]
    total_count: number
    query: string
  } | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadInitialData()
    }
  }, [isOpen])

  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery)
    }
  }, [initialQuery])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [popularResponse, categoriesResponse] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/help/popular?limit=5`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/help/categories`)
      ])
      
      const popularData = await popularResponse.json()
      const categoriesData = await categoriesResponse.json()
      
      setPopularArticles(popularData)
      setCategories(categoriesData)
    } catch (error) {
      console.error('Failed to load help data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (query: string) => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/help/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          limit: 20
        })
      })
      const data = await response.json()
      
      setSearchResults(data)
      setView('search')
    } catch (error) {
      console.error('Failed to search help articles:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCategorySelect = async (category: string) => {
    setSelectedCategory(category)
    setLoading(true)
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/help/articles?category=${encodeURIComponent(category)}&limit=50`)
      const data = await response.json()
      setArticles(data)
      setView('category')
    } catch (error) {
      console.error('Failed to load category articles:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleArticleSelect = async (article: HelpArticle) => {
    setLoading(true)
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/help/articles/${article.id}`)
      const data = await response.json()
      setSelectedArticle(data)
      setView('article')
    } catch (error) {
      console.error('Failed to load article:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleVote = async (articleId: number, isHelpful: boolean) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/feedback/help/articles/${articleId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_helpful: isHelpful
        })
      })
      
      // Update the article vote in state
      if (selectedArticle && selectedArticle.id === articleId) {
        setSelectedArticle(prev => prev ? {
          ...prev,
          user_vote: isHelpful,
          helpful_votes: isHelpful ? prev.helpful_votes + 1 : prev.helpful_votes,
          unhelpful_votes: !isHelpful ? prev.unhelpful_votes + 1 : prev.unhelpful_votes
        } : null)
      }
    } catch (error) {
      console.error('Failed to vote on article:', error)
    }
  }

  const handleBack = () => {
    if (view === 'article') {
      if (selectedCategory) {
        setView('category')
      } else if (searchResults) {
        setView('search')
      } else {
        setView('home')
      }
    } else if (view === 'search' || view === 'category') {
      setView('home')
      setSearchResults(null)
      setSelectedCategory(null)
    }
  }

  const renderHome = () => (
    <div className="space-y-6">
      {/* Search */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search help articles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch(searchQuery)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        />
        <Button
          onClick={() => handleSearch(searchQuery)}
          className="absolute right-2 top-1/2 transform -translate-y-1/2"
          size="sm"
        >
          Search
        </Button>
      </div>

      {/* Popular Articles */}
      {popularArticles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <StarIcon className="h-5 w-5 mr-2 text-yellow-500" />
            Popular Articles
          </h3>
          <div className="space-y-2">
            {popularArticles.map((article) => (
              <Card
                key={article.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => handleArticleSelect(article)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {article.title}
                      </h4>
                      {article.excerpt && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {article.excerpt}
                        </p>
                      )}
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge variant="secondary">{article.category}</Badge>
                        <span className="text-xs text-gray-500">
                          {article.view_count} views
                        </span>
                      </div>
                    </div>
                    <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <BookOpenIcon className="h-5 w-5 mr-2 text-blue-500" />
            Browse by Category
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {categories.map((category) => (
              <Card
                key={category}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => handleCategorySelect(category)}
              >
                <CardContent className="p-4 text-center">
                  <h4 className="font-medium text-gray-900 dark:text-white capitalize">
                    {category.replace('_', ' ')}
                  </h4>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderSearch = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Search Results
        </h3>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {searchResults?.total_count || 0} results for "{searchResults?.query}"
        </span>
      </div>

      {searchResults?.articles.length === 0 ? (
        <div className="text-center py-8">
          <QuestionMarkCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No articles found
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            Try searching with different keywords or browse by category.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {searchResults?.articles.map((article) => (
            <Card
              key={article.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleArticleSelect(article)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {article.title}
                    </h4>
                    {article.excerpt && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {article.excerpt}
                      </p>
                    )}
                    <div className="flex items-center space-x-4 mt-2">
                      <Badge variant="secondary">{article.category}</Badge>
                      <span className="text-xs text-gray-500">
                        {article.view_count} views
                      </span>
                    </div>
                  </div>
                  <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )

  const renderCategory = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
        {selectedCategory?.replace('_', ' ')} Articles
      </h3>

      {articles.length === 0 ? (
        <div className="text-center py-8">
          <BookOpenIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No articles in this category
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            Articles for this category are coming soon.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {articles.map((article) => (
            <Card
              key={article.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleArticleSelect(article)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {article.title}
                    </h4>
                    {article.excerpt && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {article.excerpt}
                      </p>
                    )}
                    <div className="flex items-center space-x-4 mt-2">
                      {article.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      <span className="text-xs text-gray-500">
                        {article.view_count} views
                      </span>
                    </div>
                  </div>
                  <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )

  const renderArticle = () => {
    if (!selectedArticle) return null

    return (
      <div className="space-y-6">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <Badge variant="secondary">{selectedArticle.category}</Badge>
            <span className="text-sm text-gray-500">
              {selectedArticle.view_count} views
            </span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {selectedArticle.title}
          </h2>
        </div>

        <div 
          className="prose dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: selectedArticle.content || '' }}
        />

        {selectedArticle.tags.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tags
            </h4>
            <div className="flex flex-wrap gap-2">
              {selectedArticle.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            Was this article helpful?
          </h4>
          <div className="flex items-center space-x-4">
            <Button
              variant={selectedArticle.user_vote === true ? "primary" : "ghost"}
              size="sm"
              onClick={() => handleVote(selectedArticle.id, true)}
              className="flex items-center"
            >
              <HandThumbUpIcon className="h-4 w-4 mr-1" />
              Yes ({selectedArticle.helpful_votes})
            </Button>
            <Button
              variant={selectedArticle.user_vote === false ? "primary" : "ghost"}
              size="sm"
              onClick={() => handleVote(selectedArticle.id, false)}
              className="flex items-center"
            >
              <HandThumbDownIcon className="h-4 w-4 mr-1" />
              No ({selectedArticle.unhelpful_votes})
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ResponsiveModal
      isOpen={isOpen}
      onClose={onClose}
      title={
        view === 'home' ? 'Help Center' :
        view === 'search' ? 'Search Results' :
        view === 'category' ? `${selectedCategory?.replace('_', ' ')} Articles` :
        selectedArticle?.title || 'Article'
      }
      size="lg"
      footer={
        view !== 'home' ? (
          <div className="flex justify-between">
            <Button variant="ghost" onClick={handleBack}>
              Back
            </Button>
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        ) : (
          <div className="flex justify-end">
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        )
      }
    >
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {view === 'home' && renderHome()}
          {view === 'search' && renderSearch()}
          {view === 'category' && renderCategory()}
          {view === 'article' && renderArticle()}
        </>
      )}
    </ResponsiveModal>
  )
}
import { useState } from 'react'
import { Card, CardHeader, CardContent, Button, Badge } from '@/components/ui'
import { 
  DocumentTextIcon, 
  CloudArrowUpIcon, 
  EyeIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { useDocumentSummary } from '@/hooks/useProfile'
import { format } from 'date-fns'

export function DocumentManager() {
  const { summary, loading, error, refetch } = useDocumentSummary()
  const [selectedType, setSelectedType] = useState<string>('all')

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getDocumentTypeColor = (type: string): "secondary" | "danger" | "warning" | "info" | "default" | "success" => {
    const typeColors: Record<string, "secondary" | "danger" | "warning" | "info" | "default" | "success"> = {
      'resume': 'info',
      'cover_letter': 'success',
      'portfolio': 'warning',
      'certificate': 'secondary',
      'transcript': 'info',
      'other': 'secondary'
    }
    return typeColors[type] || 'secondary'
  }

  const formatDocumentType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const filteredDocuments = summary?.documents?.filter((doc: any) => 
    selectedType === 'all' || doc.document_type === selectedType
  ) || []

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400">Error loading documents: {error}</p>
        <Button onClick={refetch} className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Document Statistics */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <DocumentTextIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Total Documents
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {summary.total_documents}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <ChartBarIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Storage Used
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatFileSize(summary.total_storage_used)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 dark:text-purple-400 font-bold text-sm">★</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Most Used
                  </p>
                  <p className="text-sm font-bold text-gray-900 dark:text-white">
                    {summary.most_used_document?.filename || 'None'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Document Type Filter */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Document Library
            </h3>
            <Button variant="primary">
              <CloudArrowUpIcon className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Type Filter Tabs */}
          <div className="flex flex-wrap gap-2 mb-6">
            <button
              onClick={() => setSelectedType('all')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedType === 'all'
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
              }`}
            >
              All ({summary?.total_documents || 0})
            </button>
            {summary && Object.entries(summary.documents_by_type).map(([type, count]) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedType === type
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                {formatDocumentType(type)} ({String(count)})
              </button>
            ))}
          </div>

          {/* Document List */}
          {filteredDocuments.length > 0 ? (
            <div className="space-y-4">
              {filteredDocuments.map((document: any) => (
                <div
                  key={document.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <DocumentTextIcon className="h-8 w-8 text-gray-400 mt-1" />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {document.filename}
                          </h4>
                          <Badge variant={getDocumentTypeColor(document.document_type)}>
                            {formatDocumentType(document.document_type)}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                          <span>{formatFileSize(document.file_size)}</span>
                          <span>Used {document.usage_count} times</span>
                          <span>
                            Uploaded {format(new Date(document.created_at), 'MMM d, yyyy')}
                          </span>
                          {document.last_used && (
                            <span>
                              Last used {format(new Date(document.last_used), 'MMM d, yyyy')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <Button variant="secondary" size="sm">
                        <EyeIcon className="h-4 w-4" />
                      </Button>
                      <Button variant="secondary" size="sm">
                        <ArrowDownTrayIcon className="h-4 w-4" />
                      </Button>
                      <Button variant="danger" size="sm">
                        <TrashIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {selectedType === 'all' 
                  ? 'No documents uploaded yet'
                  : `No ${formatDocumentType(selectedType).toLowerCase()} documents found`
                }
              </p>
              <Button variant="primary">
                <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                Upload Your First Document
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Document Usage Tips */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Document Management Tips
          </h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900 dark:text-white">Best Practices</h4>
              <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                <li>• Keep multiple versions of your resume for different roles</li>
                <li>• Use descriptive filenames (e.g., "Resume_SoftwareEngineer_2024")</li>
                <li>• Upload both PDF and Word versions when possible</li>
                <li>• Regularly update your documents with new skills and experience</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900 dark:text-white">Supported Formats</h4>
              <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                <li>• PDF documents (recommended for resumes)</li>
                <li>• Microsoft Word (.docx)</li>
                <li>• Plain text files (.txt)</li>
                <li>• Images (.jpg, .png) for portfolios</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
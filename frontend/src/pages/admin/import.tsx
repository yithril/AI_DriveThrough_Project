import { useState } from 'react'
import { useSession, getCsrfToken } from 'next-auth/react'
import { useRouter } from 'next/router'
import { useEffect } from 'react'

export default function AdminImport() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [excelFile, setExcelFile] = useState<File | null>(null)
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [overwrite, setOverwrite] = useState(false)
  const [generateAudio, setGenerateAudio] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/admin/login')
    }
  }, [status, router])

  if (status === 'loading') {
    return <div className="p-8">Loading...</div>
  }

  if (!session) {
    return null
  }

  const handleImageFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setImageFiles(files)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!excelFile) return

    setLoading(true)
    setResult('')

    try {
      // Get CSRF token
      const csrfToken = await getCsrfToken()
      if (!csrfToken) {
        throw new Error('No CSRF token')
      }

      // Create form data
      const formData = new FormData()
      formData.append('excel_file', excelFile)
      
      // Add image files
      imageFiles.forEach((file) => {
        formData.append('images', file)
      })
      
      formData.append('overwrite', overwrite.toString())
      formData.append('generate_audio', generateAudio.toString())

      // Get API base URL
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

      // Submit to backend
      const response = await fetch(`${apiBaseUrl}/admin/import`, {
        method: 'POST',
        headers: {
          'X-XSRF-Token': csrfToken,
        },
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        setResult(`✅ Import successful! ${JSON.stringify(data, null, 2)}`)
      } else {
        setResult(`❌ Import failed: ${data.detail || 'Unknown error'}`)
      }
    } catch (error) {
      setResult(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Restaurant Import</h1>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Excel File */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Excel File
              </label>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => setExcelFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                required
              />
            </div>

            {/* Image Files */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Image Files (Optional)
              </label>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageFilesChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              {imageFiles.length > 0 && (
                <p className="mt-2 text-sm text-gray-600">
                  {imageFiles.length} image(s) selected
                </p>
              )}
            </div>

            {/* Options */}
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="overwrite"
                  checked={overwrite}
                  onChange={(e) => setOverwrite(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="overwrite" className="ml-2 block text-sm text-gray-900">
                  Overwrite existing data
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="generateAudio"
                  checked={generateAudio}
                  onChange={(e) => setGenerateAudio(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="generateAudio" className="ml-2 block text-sm text-gray-900">
                  Generate audio phrases
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !excelFile}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Importing...' : 'Import Restaurant Data'}
            </button>
          </form>

          {/* Result */}
          {result && (
            <div className="mt-6 p-4 bg-gray-100 rounded-md">
              <pre className="text-sm whitespace-pre-wrap">{result}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
})

export function uploadPdf(formData) {
  return api.post('/pdf/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function fetchMarkdown(id) {
  return api.get(`/pdf/${id}/markdown`)
}

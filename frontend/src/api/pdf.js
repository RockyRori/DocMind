import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL
})

// 批量上传 PDF 文件接口
export function uploadPdfs(formData) {
    return api.post('/files/batch', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

// 获取文件列表
export function fetchDocs() {
    return api.get('/files')
}

// 批量删除文档接口
export function deleteDocs(fileBase, pdfName) {
    const base = encodeURIComponent(fileBase)
    const name = encodeURIComponent(pdfName)
    return api.delete(`/files/${base}/${name}`)
}

import axios from 'axios'


const api = axios.create({
    baseURL: 'http://172.20.41.146:5000/api'
    //    baseURL: import.meta.env.VITE_API_BASE_URL // '/api'
})


export function uploadPdf(formData) {
    return api.post('/files', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function fetchDocs() {
    return api.get('/files')
}

export function deleteDoc(fileBase, pdfName) {
    return api.delete(`/files/${encodeURIComponent(fileBase)}/${encodeURIComponent(pdfName)}`)
}

// 不再需要前端主动调用 downloadDocMd，DocumentList 用 md_url 直接下载
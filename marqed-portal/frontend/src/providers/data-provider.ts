import { DataProvider } from '@refinedev/core'
import { axiosInstance } from './axios'

const API_URL = '/api'

export const dataProvider: DataProvider = {
  getList: async ({ resource, pagination, filters, sorters }) => {
    const { current = 1, pageSize = 10 } = pagination ?? {}

    const params = new URLSearchParams()
    params.append('page', String(current))
    params.append('page_size', String(pageSize))

    // Handle filters
    filters?.forEach((filter) => {
      if ('field' in filter && filter.value !== undefined) {
        params.append(`filter[${filter.field}]`, String(filter.value))
      }
    })

    // Handle sorting
    sorters?.forEach((sorter) => {
      const order = sorter.order === 'desc' ? '-' : ''
      params.append('sort', `${order}${sorter.field}`)
    })

    const response = await axiosInstance.get(`${API_URL}/${resource}?${params}`)

    return {
      data: response.data.data,
      total: response.data.total,
    }
  },

  getOne: async ({ resource, id }) => {
    const response = await axiosInstance.get(`${API_URL}/${resource}/${id}`)
    return { data: response.data }
  },

  create: async ({ resource, variables }) => {
    const response = await axiosInstance.post(`${API_URL}/${resource}`, variables)
    return { data: response.data }
  },

  update: async ({ resource, id, variables }) => {
    const response = await axiosInstance.patch(
      `${API_URL}/${resource}/${id}`,
      variables
    )
    return { data: response.data }
  },

  deleteOne: async ({ resource, id }) => {
    const response = await axiosInstance.delete(`${API_URL}/${resource}/${id}`)
    return { data: response.data }
  },

  getApiUrl: () => API_URL,

  custom: async ({ url, method, filters, sorters, payload, query, headers }) => {
    let requestUrl = `${url}`

    if (query) {
      const params = new URLSearchParams(query as Record<string, string>)
      requestUrl = `${requestUrl}?${params}`
    }

    const response = await axiosInstance({
      method: method as string,
      url: requestUrl,
      data: payload,
      headers,
    })

    return { data: response.data }
  },
}

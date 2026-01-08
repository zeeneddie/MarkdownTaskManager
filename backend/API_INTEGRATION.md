# Frontend Integration Guide

This guide explains how to integrate the FastAPI backend with your existing frontend (project-manager.html and task-manager.html).

## Overview

The integration involves replacing File System Access API calls with REST API calls to the backend. The frontend logic remains 95% the same - only the data loading/saving layer changes.

## Architecture

```
┌─────────────────────────┐
│  Frontend (HTML/JS)     │
│  - UI Components        │
│  - Business Logic       │
│  - Event Handlers       │
└────────┬────────────────┘
         │ HTTP/REST API
         │ (fetch calls)
┌────────┴────────────────┐
│  FastAPI Backend        │
│  - REST Endpoints       │
│  - Business Logic       │
│  - Data Validation      │
└────────┬────────────────┘
         │ SQL
┌────────┴────────────────┐
│  PostgreSQL Database    │
│  - Items Table          │
│  - Sprints Table        │
│  - Users Table          │
└─────────────────────────┘
```

## Step-by-Step Integration

### 1. Create API Client Module

Create `frontend/js/api-client.js`:

```javascript
// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';
let authToken = null;

// Auth helpers
function setAuthToken(token) {
    authToken = token;
    localStorage.setItem('auth_token', token);
}

function getAuthToken() {
    if (!authToken) {
        authToken = localStorage.getItem('auth_token');
    }
    return authToken;
}

function getAuthHeaders() {
    const token = getAuthToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Generic API request handler
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers
    };

    try {
        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired, redirect to login
                window.location.href = '/login.html';
                throw new Error('Unauthorized');
            }
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Authentication API
const AuthAPI = {
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await apiRequest('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        setAuthToken(response.access_token);
        return response;
    },

    async register(email, username, password, fullName) {
        return apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                email,
                username,
                password,
                full_name: fullName
            })
        });
    },

    async getCurrentUser() {
        return apiRequest('/auth/me');
    },

    logout() {
        authToken = null;
        localStorage.removeItem('auth_token');
        window.location.href = '/login.html';
    }
};

// Epics API
const EpicsAPI = {
    async list() {
        return apiRequest('/epics/');
    },

    async get(epicId) {
        return apiRequest(`/epics/${epicId}`);
    },

    async create(data) {
        return apiRequest('/epics/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async update(epicId, data) {
        return apiRequest(`/epics/${epicId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(epicId) {
        return apiRequest(`/epics/${epicId}`, {
            method: 'DELETE'
        });
    },

    async getHierarchy(epicId) {
        return apiRequest(`/epics/${epicId}/hierarchy`);
    }
};

// Features API
const FeaturesAPI = {
    async list(epicId = null) {
        const params = epicId ? `?epic_id=${epicId}` : '';
        return apiRequest(`/features/${params}`);
    },

    async get(featureId) {
        return apiRequest(`/features/${featureId}`);
    },

    async create(data) {
        return apiRequest('/features/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async update(featureId, data) {
        return apiRequest(`/features/${featureId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(featureId) {
        return apiRequest(`/features/${featureId}`, {
            method: 'DELETE'
        });
    },

    async move(featureId, newEpicId) {
        return apiRequest(`/features/${featureId}/move?new_epic_id=${newEpicId}`, {
            method: 'POST'
        });
    }
};

// Stories API
const StoriesAPI = {
    async list(featureId = null, sprint = null) {
        const params = new URLSearchParams();
        if (featureId) params.append('feature_id', featureId);
        if (sprint) params.append('sprint', sprint);
        const queryString = params.toString();
        return apiRequest(`/stories/${queryString ? '?' + queryString : ''}`);
    },

    async get(storyId) {
        return apiRequest(`/stories/${storyId}`);
    },

    async create(data) {
        return apiRequest('/stories/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async update(storyId, data) {
        return apiRequest(`/stories/${storyId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(storyId) {
        return apiRequest(`/stories/${storyId}`, {
            method: 'DELETE'
        });
    },

    async move(storyId, newFeatureId) {
        return apiRequest(`/stories/${storyId}/move?new_feature_id=${newFeatureId}`, {
            method: 'POST'
        });
    },

    async assignSprint(storyId, sprintName) {
        return apiRequest(`/stories/${storyId}/assign-sprint?sprint_name=${sprintName}`, {
            method: 'POST'
        });
    },

    async unassignSprint(storyId) {
        return apiRequest(`/stories/${storyId}/unassign-sprint`, {
            method: 'POST'
        });
    }
};

// Tasks API
const TasksAPI = {
    async list(storyId = null) {
        const params = storyId ? `?story_id=${storyId}` : '';
        return apiRequest(`/tasks/${params}`);
    },

    async get(taskId) {
        return apiRequest(`/tasks/${taskId}`);
    },

    async create(data) {
        return apiRequest('/tasks/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async update(taskId, data) {
        return apiRequest(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(taskId) {
        return apiRequest(`/tasks/${taskId}`, {
            method: 'DELETE'
        });
    },

    async move(taskId, newStoryId) {
        return apiRequest(`/tasks/${taskId}/move?new_story_id=${newStoryId}`, {
            method: 'POST'
        });
    }
};

// Sprints API
const SprintsAPI = {
    async list(status = null) {
        const params = status ? `?status=${status}` : '';
        return apiRequest(`/sprints/${params}`);
    },

    async getActive() {
        return apiRequest('/sprints/active');
    },

    async get(sprintId) {
        return apiRequest(`/sprints/${sprintId}`);
    },

    async getWithStories(sprintId) {
        return apiRequest(`/sprints/${sprintId}/with-stories`);
    },

    async create(data) {
        return apiRequest('/sprints/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async update(sprintId, data) {
        return apiRequest(`/sprints/${sprintId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(sprintId) {
        return apiRequest(`/sprints/${sprintId}`, {
            method: 'DELETE'
        });
    },

    async start(sprintId) {
        return apiRequest(`/sprints/${sprintId}/start`, {
            method: 'POST'
        });
    },

    async complete(sprintId) {
        return apiRequest(`/sprints/${sprintId}/complete`, {
            method: 'POST'
        });
    },

    async getVelocity(sprintId) {
        return apiRequest(`/sprints/${sprintId}/velocity`);
    }
};

// Export API client
window.API = {
    Auth: AuthAPI,
    Epics: EpicsAPI,
    Features: FeaturesAPI,
    Stories: StoriesAPI,
    Tasks: TasksAPI,
    Sprints: SprintsAPI
};
```

### 2. Update project-manager.html

Replace File System Access API calls with REST API calls:

**Before (File System API):**
```javascript
async function loadProjectFile() {
    try {
        const fileHandle = await directoryHandle.getFileHandle('project.md');
        const file = await fileHandle.getFile();
        const content = await file.text();
        parseProjectFile(content);
    } catch (error) {
        console.error('Error loading project:', error);
    }
}

async function saveItem(item) {
    const markdown = generateMarkdown(item);
    const path = getItemPath(item);
    const fileHandle = await getFileHandle(path);
    const writable = await fileHandle.createWritable();
    await writable.write(markdown);
    await writable.close();
}
```

**After (REST API):**
```javascript
async function loadProjectFile() {
    try {
        showLoadingSpinner();

        // Load all epics
        const epics = await API.Epics.list();
        items = epics;

        // Load all features
        const features = await API.Features.list();
        items.push(...features);

        // Load all stories
        const stories = await API.Stories.list();
        items.push(...stories);

        // Load all tasks
        const tasks = await API.Tasks.list();
        items.push(...tasks);

        hideLoadingSpinner();
        renderHierarchy();
    } catch (error) {
        console.error('Error loading project:', error);
        showNotification('Failed to load project', 'error');
    }
}

async function saveItem(item) {
    try {
        if (item.id) {
            // Update existing item
            switch (item.type) {
                case 'epic':
                    await API.Epics.update(item.id, item);
                    break;
                case 'feature':
                    await API.Features.update(item.id, item);
                    break;
                case 'story':
                    await API.Stories.update(item.id, item);
                    break;
                case 'task':
                    await API.Tasks.update(item.id, item);
                    break;
            }
        } else {
            // Create new item
            switch (item.type) {
                case 'epic':
                    await API.Epics.create(item);
                    break;
                case 'feature':
                    await API.Features.create(item);
                    break;
                case 'story':
                    await API.Stories.create(item);
                    break;
                case 'task':
                    await API.Tasks.create(item);
                    break;
            }
        }

        showNotification('Item saved successfully', 'success');
        await loadProjectFile(); // Reload to get updated aggregations
    } catch (error) {
        console.error('Error saving item:', error);
        showNotification('Failed to save item', 'error');
    }
}
```

### 3. Add Login Page

Create `frontend/login.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login - Project Manager</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="login-container">
        <h1>Project Manager</h1>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="register.html">Register</a></p>
    </div>

    <script src="js/api-client.js"></script>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                await API.Auth.login(username, password);
                window.location.href = 'project-manager.html';
            } catch (error) {
                alert('Login failed: ' + error.message);
            }
        });
    </script>
</body>
</html>
```

### 4. Add Authentication Check

Add to the beginning of project-manager.html and task-manager.html:

```javascript
// Check authentication on page load
(async function checkAuth() {
    try {
        await API.Auth.getCurrentUser();
    } catch (error) {
        window.location.href = '/login.html';
    }
})();
```

### 5. Update Delete Function

Replace soft delete file operations with API delete:

```javascript
async function deleteItem(item) {
    if (!confirm(`Are you sure you want to delete this ${item.type}?`)) {
        return;
    }

    try {
        switch (item.type) {
            case 'epic':
                await API.Epics.delete(item.id);
                break;
            case 'feature':
                await API.Features.delete(item.id);
                break;
            case 'story':
                await API.Stories.delete(item.id);
                break;
            case 'task':
                await API.Tasks.delete(item.id);
                break;
        }

        showNotification(`${item.type} deleted successfully`, 'success');
        await loadProjectFile();
    } catch (error) {
        console.error('Error deleting item:', error);
        showNotification('Failed to delete item', 'error');
    }
}
```

### 6. Update Move Function

```javascript
async function moveItem(itemId, newParentId) {
    const item = items.find(i => i.id === itemId);

    try {
        switch (item.type) {
            case 'feature':
                await API.Features.move(itemId, newParentId);
                break;
            case 'story':
                await API.Stories.move(itemId, newParentId);
                break;
            case 'task':
                await API.Tasks.move(itemId, newParentId);
                break;
        }

        showNotification('Item moved successfully', 'success');
        await loadProjectFile();
    } catch (error) {
        console.error('Error moving item:', error);
        showNotification('Failed to move item', 'error');
    }
}
```

## Benefits of Backend Integration

1. **No Browser Limitations**: Works in all browsers (Firefox, Safari, etc.)
2. **Multi-user Support**: Multiple users can collaborate on same project
3. **Automatic Backups**: Database handles data persistence and backups
4. **Better Performance**: Optimized database queries vs. file system operations
5. **Access Control**: JWT authentication protects data
6. **Audit Trail**: Track who changed what and when
7. **Advanced Querying**: Filter and search capabilities
8. **Real-time Sync**: Potential for WebSocket real-time updates

## Migration Strategy

1. **Phase 1**: Set up backend and test with Postman/curl
2. **Phase 2**: Create API client module
3. **Phase 3**: Add authentication (login/register pages)
4. **Phase 4**: Migrate project-manager.html to use API
5. **Phase 5**: Migrate task-manager.html to use API
6. **Phase 6**: Remove File System Access API code
7. **Phase 7**: Add markdown export feature (optional)

## Testing Integration

```javascript
// Test script to verify API integration
async function testIntegration() {
    try {
        // Test login
        await API.Auth.login('testuser', 'password');
        console.log('✓ Login successful');

        // Test epic creation
        const epic = await API.Epics.create({
            title: 'Test Epic',
            status: 'PLANNED'
        });
        console.log('✓ Epic created:', epic.id);

        // Test feature creation
        const feature = await API.Features.create({
            title: 'Test Feature',
            parent_id: epic.id,
            status: 'PLANNED'
        });
        console.log('✓ Feature created:', feature.id);

        // Test cleanup
        await API.Features.delete(feature.id);
        await API.Epics.delete(epic.id);
        console.log('✓ Cleanup successful');

        console.log('All integration tests passed!');
    } catch (error) {
        console.error('Integration test failed:', error);
    }
}
```

## Error Handling

Implement proper error handling throughout:

```javascript
async function apiCallWithErrorHandling() {
    try {
        const result = await API.Epics.create(data);
        return result;
    } catch (error) {
        // Log error
        console.error('API call failed:', error);

        // Show user-friendly message
        if (error.message.includes('Unauthorized')) {
            showNotification('Session expired. Please login again.', 'error');
            API.Auth.logout();
        } else if (error.message.includes('404')) {
            showNotification('Item not found', 'error');
        } else {
            showNotification('An error occurred. Please try again.', 'error');
        }

        throw error;
    }
}
```

## Performance Optimization

1. **Caching**: Cache frequently accessed data
2. **Pagination**: Load data in pages for large datasets
3. **Debouncing**: Debounce search/filter operations
4. **Loading States**: Show spinners during API calls
5. **Optimistic Updates**: Update UI before API confirms

## Next Steps

1. Implement API client module
2. Create login/register pages
3. Update data loading functions
4. Update save/delete/move functions
5. Add error handling and loading states
6. Test thoroughly
7. Deploy!

## Support

For questions or issues with integration:
- Check API documentation: http://localhost:8000/api/docs
- Review backend logs: `docker-compose logs -f api`
- Test endpoints with Postman or curl

async function fetchWithAuth(url, options = {}) {
    let response = await fetch(url, options);
    if (response.status === 401 || response.status === 422) {
        const refreshResponse = await fetch('/refresh', { method: 'POST' });
        console.log(refreshResponse.status);
        if (refreshResponse.status !== 401) {
            response = await fetch(url, options); // повторяем запрос
        } else {
            window.location.href = '/'; // refresh тоже истёк
        }
    }
    return response;
}

async function loadImages() {
    const response = await fetchWithAuth('/images');
    const data = await response.json();
    const container = document.getElementById('images');
    container.innerHTML = '';

    if (!data.images || data.images.length === 0) {
        container.innerHTML = '<div class="empty">Изображений пока нет ¯\\_(ツ)_/¯</div>';
        return;
    }

    data.images.forEach(image => {
        const statusClass = `status-${image.status}`;
        container.innerHTML += `
            <div class="image-card">
                <div class="image-info">
                    <h3>${image.filename}</h3>
                    <div class="status ${statusClass}">Статус: ${image.status}</div>
                    <div class="status">Загружено: ${image.created_at}</div>
                </div>
                <div class="actions">
                    <button onclick="deleteImage(${image.id}, ${true})">Удалить</button>
                </div>
            </div>
        `;
    });
}

async function loadImagesRef() {
    const response = await fetchWithAuth('/refimages');
    const data = await response.json();
    const container = document.getElementById('reference');
    container.innerHTML = '';

    if (!data.images || data.images.length === 0) {
        container.innerHTML = '<div class="empty">Изображений пока нет ¯\\_(ツ)_/¯</div>';
        return;
    }

    data.images.forEach(image => {
        const statusClass = `status-${image.size}`;
        container.innerHTML += `
            <div class="image-card">
                <div class="image-info">
                    <a href="/images/${image.filename}">${image.filename}</a>
                    <div class="status ${statusClass}">Размер: ${image.size}</div>
                </div>
                <div class="actions">
                    <button onclick="deleteImage(${image.id}, ${false})">Удалить</button>
                </div>
            </div>
        `;
    });
}

async function deleteImage(id, original) {
    if (!confirm('Удалить изображение?')) return;
    if (original) {
        await fetchWithAuth(`/images/${id}`, { method: 'DELETE' });
    } else {
        await fetchWithAuth(`/reference/${id}`, { method: 'DELETE' });
    }

    loadImages();
    loadImagesRef();
}

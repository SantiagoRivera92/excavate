document.getElementById('toggle-eras').addEventListener('click', function() {
    var erasSection = document.getElementById('eras-section');
    var erasButton = document.getElementById('toggle-eras');
    if (erasSection.style.display === 'none' || erasSection.style.display === "") {
        erasSection.style.display = 'grid'; // Show the section
        erasButton.textContent = 'Hide other Time Wizard formats'
    } else {
        erasSection.style.display = 'none'; // Hide the section
        erasButton.textContent = 'Show other Time Wizard formats'
    }
});

function readPrint(file, imageUrl, isClick, printId){
    if (file === null || file.length === 0){
        updateImage("", "", isClick)
    } else {
        updateImage("https://yugipedia.com/thumb.php?f=" + file + "&w=300", imageUrl, isClick)
    }
    if (isClick){
        selectPrinting(printId)
    }
}

async function updateImage(newSrc, fallback, isClick) {
    const image = document.getElementById('card_image');
    const spinner = document.getElementById('spinner');
    const downloadButton = document.getElementById('download-image');
    if (!image.getAttribute('set-by-click') || isClick) {
        if (isClick) {
            image.setAttribute('set-by-click', 'true');
        }
        spinner.style.display = 'block';
        if (newSrc == null || newSrc.length === 0) {
            newSrc = "/static/images/no_image.png";
        }
        try {
            const response = await fetch(newSrc, { method: 'HEAD' });
            const contentType = response.headers.get('content-type');
            if (!response.ok || !contentType || !contentType.startsWith('image/')) {
                throw new Error('Invalid image');
            }
        } catch (error) {
            newSrc = fallback || "/static/images/no_image.png";
        }
        image.src = newSrc;
        downloadButton.href = newSrc;
        if (!image.hasAttribute('data-load-listener')) {
            image.addEventListener('load', hideSpinner);
            image.addEventListener('error', () => {
                if (newSrc !== fallback) {
                    updateImage(fallback, "/static/images/no_image.png");
                }
            });
            image.setAttribute('data-load-listener', 'true');
        }
    }
}

function hideSpinner() {
    const image = document.getElementById('card_image');
    const spinner = document.getElementById('spinner');
    image.setAttribute('data-load-listener', 'false')
    spinner.style.display = 'none';
}

function selectPrinting(printId) {
    const printingItems = document.querySelectorAll(".printing-item");
    clickedItem = null
    printingItems.forEach(item => {
        if (item.id === printId) {
            item.classList.toggle("clicked");
            clickedItem = item
        } else {
            item.classList.remove("clicked");
        }
    });
    if (clickedItem.classList.contains("clicked")) {
        lockImage()
    } else {
        resetImageLock()
    }
}

function lockImage(){
    const image = document.getElementById('card_image');
    image.setAttribute('set-by-click', 'true');
}

function resetImageLock(){
    const image = document.getElementById('card_image');
    image.removeAttribute("set-by-click")
}
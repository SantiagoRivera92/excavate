
function renderTable(data, isDL, isMD) {
    const tableBody = document.getElementById('printings-table-body');
    tableBody.innerHTML = '';

    if (!(isDL || isMD)){
        data.sort((a, b) => a.print_date.localeCompare(b.print_date));
    }

    lastPrint = null
    data.forEach((print, index) => {
        const row = document.createElement('tr');
        row.id = `print-${index + 1}`;
        row.className = `printing-item ${print.art_id}`;
        row.dataset.printDate = print.print_date;
        row.dataset.printRarity = print.rarity;
        row.style.cursor = 'pointer';

        if (isDL || isMD){
            const iconType = isDL ? "dl" : "md"; // Determine if it's DL or MD
            const rarity = print.rarity.toLowerCase(); // Convert rarity to lowercase to match file naming convention
            const iconPath = `/static/icon/${iconType}-${rarity}.png`; // Construct the icon path

            row.innerHTML = `<td><h4>${print.name}</h4><br/><img src="${iconPath}" alt="${print.rarity} icon"></td>`;
        } else {
            row.addEventListener('mouseover', () =>
                readPrint(print.file, print.image_url, 0, row.id)
            );
            row.addEventListener('click', () =>
                readPrint(print.file, print.image_url, 1, row.id)
            );
            row.innerHTML = `<td><h4>${print.set_name}</h4><br/>${print.set_number} (${print.rarity})<br/><br/>Print date: ${print.print_date}</td>`;
        }
        tableBody.appendChild(row);
        lastPrint = print
    });
}

function filterByPrintId(printId){
    const prints = card.sets
    filteredData = []
    lastPrint = null
    prints.forEach((print, index) => {
        lastPrint = print
        if (print.art_id == printId){
            filteredData.push(print)
        }
    })
    renderTable(filteredData, false, false)
    displayPrint(lastPrint)
}

function filterTimeWizard(date){
    const prints = card.sets
    const targetDate = new Date(date)
    lastPrint = null
    prints.forEach((print, index) => {
        printDate = new Date(print.print_date)
        if (printDate <= targetDate){
            lastPrint = print
        }
    })
    renderTable([lastPrint], false, false)
    displayPrint(lastPrint)
}

function displayCommonCharity(){
    const prints = card.sets
    filteredData = []
    lastPrint = null
    prints.forEach((print, index) => {
        lastPrint = print
        if (print.rarity === "Common"){
            filteredData.push(print)
        }
    })
    renderTable(filteredData, false, false)
    displayPrint(lastPrint)
}

function displayMasterDuel(){
    console.log("Displaying Master Duel")
    renderTable(card.md_prints, false, true)
    displayLastPrint()
}

function displayDuelLinks(){
    console.log("Displaying Duel Links")
    renderTable(card.dl_prints, true, false)
    displayLastPrint()
}

function displayAdvanced(){
    renderTable(card.sets, false, false)
    displayLastPrint()
}

function displayPrint(print){
    resetImageLock()
    readPrint(print.file, print.image_url, 0, 0)
}

function displayLastPrint(){
    const prints = card.sets
    lastPrint = null
    prints.forEach((print, index) => {
        lastPrint = print
    })
    displayPrint(lastPrint)
}

document.addEventListener('DOMContentLoaded', () => {
    renderTable(card.sets, false, false, true);
});

async function fetchConfig() {
  try {
    const res = await fetch(`${window.location.href}/config.json`)
    return res.json()
  } catch (err) {
    console.error('Failed to fetch config file')
    console.error(err)
  }
}

let popup = null
let content = null
let totalCanvas = null
let popupTitle = null
let chart = null // 차트를 저장할 변수

function renderFolderList(folders) {
  const container = document.getElementById('folder-container')
  folders.forEach(name => {
    const child = document.createElement('div')
    child.classList.add('folder-name')
    child.innerText = name

    const drawTotalChart = (csv) => {
      const header = csv[0];
      const body = csv.slice(1).reverse()
      console.log(header)
      console.log(body)

      const labels = body.map(line => line[0])
      console.log(labels)
      const ctx = totalCanvas.getContext('2d')

      if (chart) {
        chart.destroy() // 기존의 차트가 있을 경우 파괴
      }

      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Total Downloads',
            data: body.map(line => line[1]),
            borderColor: '#000',
            borderWidth: 1,
            fill: false
          }]
        }
      })

      console.log(chart)
    }

    const prepare = async () => {
      const res = await fetch(`${window.location.href}/${name}/${name}_total.csv`)
      const totalCsv = parseCsv(await res.text())
    
      popupTitle.innerText = name
      drawTotalChart(totalCsv)
      showPopup()    
    }

    child.onclick = prepare
    container.appendChild(child)
  })
}

function parseCsv(content) {
  return content
    .split('\n')
    .filter(it => it)
    .map(line => line.split(',').map(it => it.trim()))
}

function showPopup() {
  popup.classList.remove('hidden')
}

function hidePopup() {
  popup.classList.add('hidden')
}

async function start() {
  const config = await fetchConfig()
  const folderList = config.folder_list
  console.dir(folderList)

  popup = document.getElementById('popup-bg')
  content = document.getElementById('popup-content')
  totalCanvas = document.getElementById('total-canvas')
  popupTitle = document.getElementById('popup-title')

  document.getElementById('popup-close').onclick = hidePopup
  document.getElementById('popup-bg').onclick = hidePopup
  document.getElementById('popup').onclick = e => {
    e.stopPropagation()
  }
  hidePopup()

  renderFolderList(folderList)
}

document.addEventListener('DOMContentLoaded', start)

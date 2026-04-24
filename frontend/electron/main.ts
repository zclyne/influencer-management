import { app, BrowserWindow } from 'electron'

const createWindow = () => {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: new URL('./preload.ts', import.meta.url).pathname,
    },
  })

  win.loadURL(process.env.VITE_DEV_SERVER_URL ?? 'http://localhost:5173')
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})


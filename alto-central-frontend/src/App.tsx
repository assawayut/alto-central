import { AppRouter } from './router'
import { DeviceProvider } from './contexts/DeviceContext'

function App() {
  return (
    <DeviceProvider>
      <AppRouter />
    </DeviceProvider>
  )
}

export default App

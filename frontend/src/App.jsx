import { Routes, Route, Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">DSK AI Sales</h1>
      <p className="text-gray-600 mb-4">AI-помощник для отдела продаж</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Скандинавия</h2>
          <p className="text-gray-500">Комфорт-класс, 220 000 ₽/м²</p>
          <Link to="/apartments/1" className="text-blue-600 mt-4 inline-block">
            Выбрать квартиру →
          </Link>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Парк Авеню</h2>
          <p className="text-gray-500">Бизнес-класс, 290 000 ₽/м²</p>
          <Link to="/apartments/2" className="text-blue-600 mt-4 inline-block">
            Выбрать квартиру →
          </Link>
        </div>
      </div>
    </div>
  )
}

function ApartmentsPage() {
  return <div className="p-8"><h2>Список квартир</h2></div>
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/apartments/:complexId" element={<ApartmentsPage />} />
    </Routes>
  )
}

export default App

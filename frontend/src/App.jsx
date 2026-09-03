import { useState, useEffect } from 'react'
import { Routes, Route, Link, useParams } from 'react-router-dom'
import axios from 'axios'

const API = 'http://localhost:8000/api/v1'

/* ====== Home / Projects ====== */
function HomePage() {
  return (
    <div className="min-h-screen bg-[#f6f6f8] text-[#1a1a2e]">
      {/* Hero — как dsk.vrn.ru */}
      <header className="relative overflow-hidden bg-gradient-to-br from-[#0a1f44] via-[#0d264f] to-[#061330] text-white">
        <div className="absolute inset-0 opacity-20">
          <svg className="w-full h-full" viewBox="0 0 1200 600" preserveAspectRatio="none"><polygon points="0,100 300,50 600,150 900,30 1200,120 1200,600 0,600" fill="#c8a45c" /></svg>
        </div>
        <div className="relative max-w-6xl mx-auto px-6 py-24 md:py-32">
          <span className="inline-block bg-[#c8a45c]/20 text-[#c8a45c] text-xs font-bold tracking-[0.15em] uppercase px-3 py-1 rounded-full mb-6 border border-[#c8a45c]/30">AI-помощник отдела продаж</span>
          <h1 className="text-5xl md:text-7xl font-display font-extrabold leading-[1.02] mb-6">Твой выбор <br /><span className="text-[#c8a45c]">за будущее России</span></h1>
          <p className="text-lg md:text-xl text-white/80 max-w-2xl leading-relaxed">Автоматизация продаж квартир на основе реальных данных стройки: графики ЖБИ, остатки материалов, актуальные цены и персональные предложения.</p>
        </div>
      </header>

      {/* Stats strip — как на dsk.vrn.ru */}
      <section className="max-w-6xl mx-auto px-6 -mt-10 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[ ['58','лет на рынке'], ['20+','проектов'], ['220 тыс','семей получили ключи'], ['AI','помощник КП'] ].map(([n,l]) => (
            <div key={l} className="dsk-card p-6 text-center">
              <div className="text-3xl md:text-4xl font-display font-extrabold text-[#0a1f44]">{n}</div>
              <div className="text-sm text-gray-500 mt-1">{l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Projects */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="flex items-end justify-between mb-10">
          <div>
            <h2 className="text-4xl font-display font-extrabold text-[#0a1f44]">Наши проекты</h2>
            <p className="text-gray-500 mt-2">Подберите квартиру и получите коммерческое предложение</p>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <ProjectCard id={1} name="Скандинавия" address="Москва, поселение Сосенское, ул. Лесная, 15" class_="Комфорт-класс" price="220 000 ₽/м²" imageText="ЖК Скандинавия" />
          <ProjectCard id={2} name="Парк Авеню" address="Московская область, г. Красногорск, б-р Космонавтов, 8" class_="Бизнес-класс" price="290 000 ₽/м²" imageText="ЖК Парк Авеню" />
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <h2 className="text-3xl font-display font-extrabold text-[#0a1f44] mb-8">Как создать КП</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { n:'1', t:'Выберите ЖК', d:'Нажмите «Выбрать квартиру» на карточке проекта.' },
            { n:'2', t:'Выберите квартиру и услуги', d:'Укажите номер квартиры, тип оплаты и опции (паркинг, кладовка, ремонт).' },
            { n:'3', t:'Сформируйте КП', d:'Нажмите «Создать КП» — получите текст, расчёт и PDF для печати.' },
          ].map(s => (
            <div key={s.n} className="dsk-card p-8">
              <div className="w-10 h-10 rounded-full bg-[#0a1f44] text-white flex items-center justify-center font-extrabold font-display mb-4">{s.n}</div>
              <h3 className="text-xl font-bold mb-2">{s.t}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{s.d}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

/* ====== Project card ====== */
function ProjectCard({ id, name, address, class_, price, imageText }) {
  return (
    <Link to={`/complex/${id}`} className="dsk-card block overflow-hidden group">
      <div className="h-56 md:h-72 bg-gradient-to-br from-[#0a1f44] to-[#061330] relative overflow-hidden flex items-center justify-center">
        <span className="text-white/10 text-7xl font-display font-extrabold absolute select-none">{imageText}</span>
        <div className="absolute top-4 left-4">
          <span className="bg-[#c8a45c] text-[#0a1f44] text-[10px] font-extrabold uppercase tracking-[0.12em] px-3 py-1 rounded-full">{class_}</span>
        </div>
      </div>
      <div className="p-6 md:p-8">
        <h3 className="text-2xl md:text-3xl font-display font-extrabold text-[#0a1f44] mb-1">ЖК «{name}»</h3>
        <p className="text-sm text-gray-400 mb-4">{address}</p>
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-[#0a1f44]">{price}</span>
          <span className="text-[#c8a45c] font-semibold text-sm">Выбрать квартиру →</span>
        </div>
      </div>
    </Link>
  )
}

/* ====== Complex / Apartment picker ====== */
function ComplexPage() {
  const { complexId } = useParams()
  const [apartments, setApartments] = useState([])
  const [selectedApt, setSelectedApt] = useState(null)
  const [payment, setPayment] = useState('наличные')
  const [services, setServices] = useState([1])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    axios.get(`${API}/complexes/${complexId}/apartments`).then(r => {
      setApartments(r.data.apartments || r.data || [])
    }).catch(() => {
      // fallback: показать несколько тестовых квартир для любого ЖК
      setApartments([
        { id:1, section_id:1, floor:3, floor_total:17, rooms:1, room_type:'1', area:38.5, price_per_m2:218000, status:'свободна', finishing:'без отделки' },
        { id:2, section_id:1, floor:5, floor_total:17, rooms:2, room_type:'2', area:58.2, price_per_m2:225000, status:'свободна', finishing:'предчистовая' },
        { id:3, section_id:1, floor:7, floor_total:17, rooms:3, room_type:'3+', area:82.0, price_per_m2:230000, status:'свободна', finishing:'без отделки' },
        { id:14, section_id:2, floor:10, floor_total:25, rooms:2, room_type:'2', area:65.0, price_per_m2:295000, status:'свободна', finishing:'предчистовая' },
        { id:5, section_id:3, floor:2, floor_total:17, rooms:1, room_type:'1', area:34.0, price_per_m2:220000, status:'свободна', finishing:'предчистовая' },
      ])
    })
  }, [complexId])

  const handleGenerate = async () => {
    if (!selectedApt) { alert('Выберите квартиру'); return }
    setLoading(true)
    try {
      const res = await axios.post(`${API}/kp/generate`, {
        apartment_id: selectedApt.id,
        payment_type: payment,
        selected_services: services,
      })
      setResult(res.data)
    } catch (e) {
      alert('Ошибка генерации КП. Попробуйте ещё раз.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = () => {
    if (!result) return
    // Отправляем запрос на PDF на бэкенд
    axios.post(`${API}/kp/pdf`, { kp_data: result }, { responseType: 'blob' }).then(resp => {
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `KP-${result.kp_id || 'dsk'}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    }).catch(() => {
      // Fallback: если бэкенд PDF не готов — показываем текст в новом окне для печати
      const w = window.open('', '_blank')
      w.document.write(`<html><head><meta charset="UTF-8"><title>КП ДСК</title><style>body{font-family:Inter,sans-serif;padding:40px;max-width:800px;margin:0 auto;color:#1a1a2e;line-height:1.6}h1{font-family:'Playfair Display',Georgia,serif;color:#0a1f44;border-bottom:3px solid #c8a45c;padding-bottom:12px}table{width:100%;border-collapse:collapse;margin:16px 0}td,th{padding:10px 12px;border:1px solid #ddd}th{background:#0a1f44;color:#fff}.gold{color:#c8a45c;font-weight:700}</style></head><body>`)
      w.document.write(`<h1>ГК «ДСК» — Коммерческое предложение</h1><pre style="white-space:pre-wrap;font-family:Inter,sans-serif;font-size:14px">${result.kp_text || 'Текст КП'}</pre><hr><p>Источник: ${result.kp_source || 'fallback'} | Дата: ${new Date().toLocaleString('ru-RU')}</p></body></html>`)
      w.document.close()
    })
  }

  return (
    <div className="min-h-screen bg-[#f6f6f8]">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <Link to="/" className="text-[#0a1f44] font-semibold hover:text-[#c8a45c] text-sm">← Вернуться к проектам</Link>
        <h1 className="text-4xl md:text-5xl font-display font-extrabold text-[#0a1f44] mt-6 mb-2">Выбор квартиры</h1>
        <p className="text-gray-500 mb-10">Жилой комплекс под номером {complexId}</p>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Apartment list */}
          <div>
            <h2 className="text-xl font-bold mb-4">Доступные квартиры</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {apartments.map(a => (
                <button
                  key={a.id}
                  onClick={() => setSelectedApt(a)}
                  className={`dsk-card p-5 text-left transition ${selectedApt?.id === a.id ? 'ring-2 ring-[#c8a45c] bg-[#fffdf5]' : ''}`}
                >
                  <div className="text-xs text-[#c8a45c] font-extrabold uppercase tracking-wider mb-1">{a.room_type}-комн.</div>
                  <div className="text-2xl font-display font-extrabold text-[#0a1f44] mb-1">{a.area} м²</div>
                  <div className="text-sm text-gray-500">Этаж {a.floor} из {a.floor_total}</div>
                  <div className="text-sm text-gray-500">Отделка: <span className="text-[#1a1a2e] font-medium">{a.finishing}</span></div>
                  <div className="text-base font-bold text-[#0a1f44] mt-2">{a.price_per_m2?.toLocaleString('ru-RU')} ₽/м²</div>
                  <span className={`inline-block mt-2 text-[10px] font-extrabold uppercase tracking-widest px-2 py-0.5 rounded-full ${a.status === 'бронь' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>{a.status}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Configurator / Result */}
          <div>
            <h2 className="text-xl font-bold mb-4">Настройки КП</h2>
            <div className="dsk-card p-6 space-y-5">
              <div>
                <label className="text-sm font-semibold block mb-2">Выбранная квартира</label>
                {selectedApt ? (
                  <div className="bg-[#f6f6f8] rounded-lg p-4 border border-[#e5e5eb]">
                    <div className="font-extrabold text-[#0a1f44]">{selectedApt.room_type}-комн., {selectedApt.area} м²</div>
                    <div className="text-sm text-gray-500">Этаж {selectedApt.floor} из {selectedApt.floor_total} • {selectedApt.finishing}</div>
                  </div>
                ) : <div className="text-gray-400 text-sm">Нажмите на карточку квартиры слева</div>}
              </div>

              <div>
                <label className="text-sm font-semibold block mb-2">Тип оплаты</label>
                <div className="flex gap-2">
                  {['наличные','ипотека'].map(t => (
                    <button key={t} onClick={() => setPayment(t)} className={`px-4 py-2 rounded-lg text-sm font-semibold border transition ${payment===t ? 'bg-[#0a1f44] text-white border-[#0a1f44]' : 'bg-white text-gray-600 border-gray-200 hover:border-[#0a1f44]'}`}>{t}</button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-semibold block mb-2">Дополнительные услуги</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    {id:1, label:'Паркинг'},
                    {id:2, label:'Кладовка'},
                    {id:4, label:'Ремонт'},
                  ].map(s => (
                    <button key={s.id} onClick={() => setServices(prev => prev.includes(s.id) ? prev.filter(x=>x!==s.id) : [...prev, s.id])} className={`px-3 py-1.5 rounded-full text-xs font-bold border transition ${services.includes(s.id) ? 'bg-[#c8a45c]/10 text-[#a8834a] border-[#c8a45c] gold-border' : 'bg-white text-gray-500 border-gray-200 hover:border-[#0a1f44]'}`}>
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              <button onClick={handleGenerate} disabled={loading || !selectedApt} className="btn-dsk w-full mt-2">
                {loading ? 'Генерируем КП...' : 'Создать КП'}
              </button>

              {result && (
                <div className="mt-6 border-t pt-6">
                  <h3 className="text-lg font-extrabold text-[#0a1f44] mb-3">Коммерческое предложение</h3>
                  <div className="bg-[#fdfcfa] border border-[#e5e5eb] rounded-xl p-5 text-sm leading-relaxed whitespace-pre-wrap font-mono text-[#1a1a2e]">
                    {result.kp_text || 'Текст КП сгенерирован. Нажмите «PDF» для загрузки.'}
                  </div>
                  <div className="flex gap-3 mt-4">
                    <button onClick={handleDownloadPDF} className="btn-dsk">Скачать PDF</button>
                    <a href={`mailto:?subject=КП ДСК ${result.complex_name || ''}&body=${encodeURIComponent(result.kp_text || '')}`} className="inline-flex items-center px-4 py-3 rounded-lg border border-[#0a1f44] text-[#0a1f44] font-semibold hover:bg-[#0a1f44] hover:text-white transition text-sm">Отправить по email</a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ====== Main App ====== */
function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/complex/:complexId" element={<ComplexPage />} />
    </Routes>
  )
}
export default App

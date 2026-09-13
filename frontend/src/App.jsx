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
        <div className="mt-10 dsk-card p-6 md:p-8 bg-gradient-to-r from-[#0a1f44] to-[#061330] text-white">
          <h3 className="text-2xl font-display font-extrabold mb-4">Поддержка менеджера и анализ конкурентов</h3>
          <div className="grid sm:grid-cols-2 gap-4 text-sm text-[#1a1a2e]/90">
            <div><strong className="text-[#c8a45c]">Анализ диалогов</strong> — выявление типовых возражений («дорого», «риски сроков», «услуги») и готовые рекомендации для повышения конверсии.</div>
            <div><strong className="text-[#c8a45c]">Конкуренты</strong> — сравнение цен и готовности объектов в том же районе (жк «Европейский», «Крымский квартал»).</div>
          </div>
          <div className="mt-4 text-xs text-white/50">API: POST /api/v1/manager/analyze · GET /api/v1/competitors</div>
        </div>
      </section>

      {/* Active Manager Support + Competitors */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <h2 className="text-3xl font-display font-extrabold text-[#0a1f44] mb-6">Поддержка менеджера</h2>
        <ManagerSupportBlock />
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
  const [typedText, setTypedText] = useState('')
  const [typingDone, setTypingDone] = useState(false)

  useEffect(() => {
    if (!result?.kp_text) return
    setTypedText('')
    setTypingDone(false)
    const full = result.kp_text
    let i = 0
    const interval = setInterval(() => {
      i += 3
      setTypedText(full.slice(0, i))
      if (i >= full.length) {
        clearInterval(interval)
        setTypingDone(true)
      }
    }, 14)
    return () => clearInterval(interval)
  }, [result?.kp_text])

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

  const handleDownloadPDF = async () => {
  if (!result?.kp_text || !selectedApt) {
    alert('Сначала сформируйте КП')
    return
  }
  try {
    const res = await axios.post(
      `${API}/kp/pdf`,
      {
        kp_text: result.kp_text,          // ← тот же текст, что в превью
        apartment_id: selectedApt.id,
        payment_type: payment,            // 'наличные' | 'ипотека'
        selected_services: services,      // [1, 4] и т.п.
      },
      { responseType: 'blob' }
    )
    const url = URL.createObjectURL(
      new Blob([res.data], { type: 'application/pdf' })
    )
    const a = document.createElement('a')
    a.href = url
    a.download = `KP-${selectedApt.id}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('PDF error', e)
    alert('Не удалось сформировать PDF')
  }
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
                  <div className="bg-gradient-to-br from-[#fdfcfa] to-[#fff8e7] border border-[#e5dcc8] rounded-2xl p-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`w-2 h-2 rounded-full ${typingDone ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                      <span className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-amber-600">{typingDone ? 'КП от GigaChat' : 'Генерация…'}</span>
                    </div>
                    <div id="kp-text-area" className="text-sm leading-loose text-[#1a1a2e] min-h-[120px]" dangerouslySetInnerHTML={{ __html: renderMarkdown(typedText || '') }} />
                  </div>
                  <div className="mt-4 flex justify-center">
                    <button onClick={handleDownloadPDF} className="btn-dsk">Скачать PDF</button>
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

function renderMarkdown(text) {
  if (!text) return '<p class="text-gray-400 italic">Нажмите «Создать КП» для генерации предложения</p>'
  let html = text
    // Headers
    .replace(/^### (.*)$/gm, '<h3 class="text-xl font-extrabold text-[#0a1f44] mt-6 mb-2">$1</h3>')
    .replace(/^## (.*)$/gm, '<h2 class="text-2xl font-extrabold text-[#0a1f44] border-b-2 border-[#c8a45c] pb-1 mt-8 mb-3">$1</h2>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold text-[#0a1f44]">$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em class="italic">$1</em>')
    // Tables (markdown pipeline style)
  const tableRegex = /\|(.+?)\|\n\|[-:|\s]+\|\n((?:\|.+?\|\n)+)/g
  html = html.replace(tableRegex, (match, header, body) => {
    const headers = header.split('|').map(s => s.trim()).filter(s => s.length > 0)
    const rows = body.trim().split('\n').map(r => r.split('|').map(s => s.trim()).filter(s => s.length > 0))
    if (headers.length === 0) return match
    let th = '<tr>' + headers.map(h => `<th class="px-2 py-1.5 text-xs font-bold uppercase tracking-wider text-[#c8a45c] bg-[#0a1f44] border-r border-[#c8a45c]/30">${h}</th>`).join('') + '</tr>'
    let tr = rows.map(r => '<tr class="hover:bg-[#f8f7f4] transition">' + r.map(c => `<td class="px-3 py-2.5 text-sm border-b border-[#e5e5eb]">${c}</td>`).join('') + '</tr>').join('')
    return `<table class="w-full border-collapse text-sm my-4 rounded-xl overflow-hidden shadow-md ring-1 ring-[#e5e5eb]/50"><thead>${th}</thead><tbody class="bg-white/60">${tr}</tbody></table>`
  })
  // Bullet lists
  html = html.replace(/^• (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    // Lines with bullet + risk -> preserve line breaks
  html = html.replace(/(• .*?)\n(?=• )/g, '$1<br>')
  // Paragraph breaks
  html = html.split('\n\n').map(p => p.trim() ? `<p class="mb-2">${p}</p>` : '').join('')
  return html
}

/* ====== Manager Support Block (active) ====== */
function ManagerSupportBlock() {
  const [dialogText, setDialogText] = useState('Клиент говорит: это дорого, и я боюсь что сдвинут сроки')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)

  const [typedResult, setTypedResult] = useState('')
  const [typingDone, setTypingDone] = useState(false)

  const runAnalyze = async () => {
    setLoading(true)
    setTypedResult('')
    setTypingDone(false)
    try {
      const r = await axios.post(`${API}/manager/analyze`, { dialog_text: dialogText })
      setAnalysis(r.data)
      // Формируем текст для печати
      const lines = []
      lines.push(`Выявлено возражений: ${r.data.detected_objections}`)
      lines.push(`Источник: ${r.data.source || 'local_db'}`)
      for (const o of r.data.objections || []) {
        lines.push(`\n► ${o.type}  (триггер: «${o.trigger || o.trigger_word || '—'}»)`)
        lines.push(`  → ${o.response || ''}`)
        lines.push(`  💡 ${o.conversion_tip || ''}`)
      }
      for (const tip of r.data.conversion_tips || []) {
        lines.push(`\n• ${tip}`)
      }
      const full = lines.join('\n')
      let i = 0
      const interval = setInterval(() => {
        i += 2
        setTypedResult(full.slice(0, i))
        if (i >= full.length) {
          clearInterval(interval)
          setTypingDone(true)
        }
      }, 12)
    } catch (e) {
      alert('Ошибка анализа. Проверьте подключение к серверу.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Analysis */}
      <div className="dsk-card p-6 md:p-8">
        <h3 className="text-xl font-extrabold text-[#0a1f44] mb-2">Анализ диалога</h3>
        <p className="text-sm text-gray-500 mb-4">Введите текст диалога — система выявит возражения и предложит рекомендации.</p>
        <textarea
          className="w-full rounded-xl border border-[#e5e5eb] p-4 text-sm text-[#1a1a2e] focus:outline-none focus:ring-2 focus:ring-[#c8a45c]/40 mb-4 min-h-[120px] resize-y"
          value={dialogText}
          onChange={e => setDialogText(e.target.value)}
        />
        <button onClick={runAnalyze} disabled={loading} className="btn-dsk w-full">
          {loading ? 'Анализируем…' : 'Проанализировать диалог'}
        </button>
        {analysis && (
          <div className="mt-6 space-y-4">
            {/* Красивый результат — карточки */}
            <div className="bg-gradient-to-br from-[#fffdf5] via-[#fff] to-[#fff8e7] border border-[#e5dcc8] rounded-2xl p-6 shadow-md">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-display font-extrabold text-[#0a1f44] text-xl">Результат анализа</h4>
                <span className="text-xs font-bold bg-[#0a1f44] text-white px-3 py-1 rounded-full">{analysis.source === 'gigachat' ? 'GigaChat' : 'DB'}</span>
              </div>
              <div className="text-sm text-gray-500 mb-4">Возражений найдено: <strong className="text-[#0a1f44] text-lg">{analysis.detected_objections}</strong></div>

              {analysis.objections.map((o, i) => (
                <div key={i} className="mb-4 last:mb-0 bg-white/70 rounded-xl p-4 border border-[#e5e5eb] shadow-sm">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#0a1f44] to-[#c8a45c] text-white flex items-center justify-center font-extrabold text-xs shadow-md">{i + 1}</div>
                    <div>
                      <strong className="text-[#0a1f44] font-extrabold text-base">{o.type || o.objection_type || '—'}</strong>
                      <span className="text-xs text-[#c8a45c] font-bold ml-2">триггер: «{o.trigger || o.trigger_word || '—'}»</span>
                    </div>
                  </div>
                  <p className="text-sm text-[#1a1a2e] leading-relaxed mb-2">{o.response}</p>
                  <p className="text-xs text-emerald-700 font-semibold bg-emerald-50 inline-block px-2 py-0.5 rounded-md">💡 {o.conversion_tip}</p>
                </div>
              ))}

              <div className="mt-4 pt-4 border-t border-[#e5dcc8]">
                <h5 className="text-xs font-extrabold uppercase tracking-widest text-[#c8a45c] mb-2">Рекомендации для конверсии</h5>
                <div className="flex flex-wrap gap-2">
                  {(analysis.conversion_tips || []).map((tip, i) => (
                    <span key={i} className="text-xs bg-[#0a1f44] text-white px-3 py-1.5 rounded-lg font-medium shadow-sm">→ {tip}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Competitors */}
      <div className="dsk-card p-6 md:p-8">
        <h3 className="text-xl font-extrabold text-[#0a1f44] mb-2">Конкуренты в районе</h3>
        <CompetitorsBlock />
      </div>
    </div>
  )
}

function CompetitorsBlock() {
  const [district, setDistrict] = useState('Новая Москва')
  const [data, setData] = useState(null)
  useEffect(() => {
    axios.get(`${API}/competitors`, { params: { district } }).then(r => setData(r.data)).catch(() => setData({ district, competitors: [
      { name: 'ЖК «Европейский»', price: '265 000 ₽/м²', readiness: '72%', notes: 'Паркинг включён, ипотека 7%' },
      { name: 'ЖК «Крымский квартал»', price: '255 000 ₽/м²', readiness: '61%', notes: 'Готовность ниже, но рассрочка 0%' },
    ]}))
  }, [district])
  return (
    <div>
      <div className="flex gap-2 mb-4">
        {['Новая Москва', 'Красногорск', 'Химки'].map(d => (
          <button key={d} onClick={() => setDistrict(d)} className={`px-3 py-1 rounded-full text-xs font-bold border transition ${district===d ? 'bg-[#0a1f44] text-white border-[#0a1f44]' : 'bg-white text-gray-500 border-gray-200'}`}>{d}</button>
        ))}
      </div>
      {data && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-[#c8a45c]">
                <th className="text-left py-2 font-extrabold text-[#0a1f44]">Объект</th>
                <th className="text-left py-2 font-extrabold text-[#0a1f44]">Цена</th>
                <th className="text-left py-2 font-extrabold text-[#0a1f44]">Готовность</th>
                <th className="text-left py-2 font-extrabold text-[#0a1f44]">Особенности</th>
              </tr>
            </thead>
            <tbody>
              {data.competitors.map((c, i) => {
                const base = 245000; // базовая цена для сравнения (эталон ДСК)
                const diff = c.price_per_m2 - base
                const arrow = diff > 0 ? '▲' : diff < 0 ? '▼' : '—'
                const color = diff > 0 ? 'text-rose-500' : diff < 0 ? 'text-emerald-600' : 'text-gray-400'
                return (
                <tr key={i} className="border-b border-[#e5e5eb] hover:bg-[#f8f7f4]">
                  <td className="py-2.5 font-bold text-[#0a1f44]">{c.name}<br/><span className="text-[10px] text-gray-400 font-normal">{c.address?.split(',')[0] || ''}</span></td>
                  <td className="py-2.5 text-[#1a1a2e] font-bold">{c.price_per_m2?.toLocaleString('ru-RU')} ₽/м² <span className={`text-xs font-extrabold ${color}`}>{arrow} {Math.abs(diff).toLocaleString('ru-RU')}</span></td>
                  <td className="py-2.5 text-[#1a1a2e]">{c.readiness || c.progress + '%'}</td>
                  <td className="py-2.5 text-gray-500 text-xs">{c.notes || c.class_}</td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      )}
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

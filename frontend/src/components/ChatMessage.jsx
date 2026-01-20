import React from 'react'
import ResultCard from './ResultCard'

function ChatMessage({ message, onExampleClick }) {
  const { type, content, examples, results, extractedParams, isError } = message

  const formatParamName = (key) => {
    const names = {
      rating_kva: 'Güç',
      high_voltage_v: 'YG',
      low_voltage_v: 'AG',
      frequency_hz: 'Frekans',
      vector_group: 'Bağlantı',
      no_load_loss_w: 'P0',
      load_loss_w: 'Pk',
      impedance_percent: 'Ucc',
      cooling_type: 'Soğutma',
      lv_material: 'AG Malz.',
      hv_material: 'YG Malz.'
    }
    return names[key] || key
  }

  const formatParamValue = (key, value) => {
    if (key.includes('_v')) return `${value}V`
    if (key.includes('_w')) return `${value}W`
    if (key.includes('_hz')) return `${value}Hz`
    if (key.includes('_kva')) return `${value}kVA`
    if (key.includes('_percent')) return `${value}%`
    return value
  }

  return (
    <div className={`message ${type}`}>
      <div className="avatar">
        {type === 'user' ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        )}
      </div>

      <div className={`message-content ${isError ? 'error' : ''}`}>
        <p>{content}</p>

        {examples && (
          <div className="examples">
            {examples.map((example, idx) => (
              <button
                key={idx}
                className="example-chip"
                onClick={() => onExampleClick(example)}
              >
                {example}
              </button>
            ))}
          </div>
        )}

        {extractedParams && Object.keys(extractedParams).length > 0 && (
          <div className="extracted-params">
            <h4>Çıkarılan Parametreler</h4>
            <div className="param-list">
              {Object.entries(extractedParams).map(([key, value]) => (
                <span key={key} className="param-tag">
                  {formatParamName(key)}: {formatParamValue(key, value)}
                </span>
              ))}
            </div>
          </div>
        )}

        {results && results.length > 0 && (
          <div className="results">
            {results.map((result, idx) => (
              <ResultCard key={idx} result={result} rank={idx + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessage

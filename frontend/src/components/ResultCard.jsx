import React, { useState } from 'react'

function ResultCard({ result, rank }) {
  const [expanded, setExpanded] = useState(false)
  const { design_number, file_path, similarity_score, specs, match_details } = result

  const scorePercent = (similarity_score * 100).toFixed(1)
  const scoreClass = similarity_score >= 0.8 ? 'high' : similarity_score >= 0.5 ? 'medium' : 'low'

  const mainSpecs = [
    { label: 'Güç', value: specs.rating_kva, unit: 'kVA' },
    { label: 'YG', value: specs.high_voltage_v, unit: 'V' },
    { label: 'AG', value: specs.low_voltage_v, unit: 'V' },
    { label: 'Bağlantı', value: specs.vector_group, unit: '' },
    { label: 'P0', value: specs.no_load_loss_w, unit: 'W' },
    { label: 'Pk', value: specs.load_loss_w, unit: 'W' },
    { label: 'Ucc', value: specs.impedance_percent, unit: '%' },
    { label: 'Soğutma', value: specs.cooling_type, unit: '' }
  ].filter(s => s.value !== null && s.value !== undefined)

  return (
    <div className="result-card" onClick={() => setExpanded(!expanded)}>
      <div className="result-header">
        <div>
          <span style={{ color: '#71717a', marginRight: '0.5rem' }}>#{rank}</span>
          <span className="result-title">{design_number}</span>
        </div>
        <span className={`result-score ${scoreClass}`}>
          %{scorePercent} Eşleşme
        </span>
      </div>

      <div className="result-specs">
        {mainSpecs.map((spec, idx) => (
          <div key={idx} className="spec-item">
            <span className="spec-label">{spec.label}</span>
            <span className="spec-value">
              {spec.value}{spec.unit}
            </span>
          </div>
        ))}
      </div>

      {expanded && (
        <>
          <div className="result-path">
            <strong>Dosya:</strong> {file_path}
          </div>

          {match_details && Object.keys(match_details).length > 0 && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
              <strong style={{ color: '#60a5fa' }}>Eşleşme Detayları:</strong>
              <div style={{ marginTop: '0.5rem', display: 'grid', gap: '0.25rem' }}>
                {Object.entries(match_details).map(([key, detail]) => (
                  <div key={key} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '0.25rem 0.5rem',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '0.25rem'
                  }}>
                    <span style={{ color: '#a1a1aa' }}>{key}</span>
                    <span>
                      Aranan: {detail.query} | Dizayn: {detail.design || '-'} |
                      <span style={{
                        color: detail.score >= 0.8 ? '#4ade80' : detail.score >= 0.5 ? '#fbbf24' : '#f87171'
                      }}> %{(detail.score * 100).toFixed(0)}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <div style={{
        marginTop: '0.5rem',
        textAlign: 'center',
        fontSize: '0.7rem',
        color: '#71717a'
      }}>
        {expanded ? '▲ Daralt' : '▼ Detaylar için tıkla'}
      </div>
    </div>
  )
}

export default ResultCard

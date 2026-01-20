import React, { useState, useEffect } from 'react'

function SearchForm({ onSearch, isLoading, stats }) {
  const [formData, setFormData] = useState({
    rating_kva: '',
    high_voltage_v: '',
    low_voltage_v: '',
    vector_group: '',
    cooling_type: '',
    hv_material: '',
    lv_material: '',
    impedance_percent: '',
    max_no_load_loss_w: '',
    max_load_loss_w: '',
    max_results: 10
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    // Boş olmayan değerleri filtrele ve sayılara dönüştür
    const searchParams = {}

    if (formData.rating_kva) searchParams.rating_kva = parseFloat(formData.rating_kva)
    if (formData.high_voltage_v) searchParams.high_voltage_v = parseFloat(formData.high_voltage_v)
    if (formData.low_voltage_v) searchParams.low_voltage_v = parseFloat(formData.low_voltage_v)
    if (formData.vector_group) searchParams.vector_group = formData.vector_group
    if (formData.cooling_type) searchParams.cooling_type = formData.cooling_type
    if (formData.hv_material) searchParams.hv_material = formData.hv_material
    if (formData.lv_material) searchParams.lv_material = formData.lv_material
    if (formData.impedance_percent) searchParams.impedance_percent = parseFloat(formData.impedance_percent)
    if (formData.max_no_load_loss_w) searchParams.max_no_load_loss_w = parseFloat(formData.max_no_load_loss_w)
    if (formData.max_load_loss_w) searchParams.max_load_loss_w = parseFloat(formData.max_load_loss_w)
    searchParams.max_results = parseInt(formData.max_results) || 10

    onSearch(searchParams)
  }

  const handleClear = () => {
    setFormData({
      rating_kva: '',
      high_voltage_v: '',
      low_voltage_v: '',
      vector_group: '',
      cooling_type: '',
      hv_material: '',
      lv_material: '',
      impedance_percent: '',
      max_no_load_loss_w: '',
      max_load_loss_w: '',
      max_results: 10
    })
  }

  const hasAnyValue = Object.entries(formData).some(([key, value]) =>
    key !== 'max_results' && value !== ''
  )

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-section">
        <h3>Temel Parametreler</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="rating_kva">Guc (kVA)</label>
            <input
              type="number"
              id="rating_kva"
              name="rating_kva"
              value={formData.rating_kva}
              onChange={handleChange}
              placeholder="ornek: 630"
              min="0"
              step="any"
            />
          </div>
          <div className="form-group">
            <label htmlFor="high_voltage_v">YG Gerilim (V)</label>
            <input
              type="number"
              id="high_voltage_v"
              name="high_voltage_v"
              value={formData.high_voltage_v}
              onChange={handleChange}
              placeholder="ornek: 10000"
              min="0"
              step="any"
            />
          </div>
          <div className="form-group">
            <label htmlFor="low_voltage_v">AG Gerilim (V)</label>
            <input
              type="number"
              id="low_voltage_v"
              name="low_voltage_v"
              value={formData.low_voltage_v}
              onChange={handleChange}
              placeholder="ornek: 400"
              min="0"
              step="any"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Baglanti ve Malzeme</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="vector_group">Vektor Grubu</label>
            <select
              id="vector_group"
              name="vector_group"
              value={formData.vector_group}
              onChange={handleChange}
            >
              <option value="">Hepsi</option>
              {stats?.vector_groups?.map(vg => (
                <option key={vg} value={vg}>{vg}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="cooling_type">Sogutma Tipi</label>
            <select
              id="cooling_type"
              name="cooling_type"
              value={formData.cooling_type}
              onChange={handleChange}
            >
              <option value="">Hepsi</option>
              {stats?.cooling_types?.map(ct => (
                <option key={ct} value={ct}>{ct}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="hv_material">YG Malzeme</label>
            <select
              id="hv_material"
              name="hv_material"
              value={formData.hv_material}
              onChange={handleChange}
            >
              <option value="">Hepsi</option>
              {stats?.materials?.hv?.map(m => (
                <option key={m} value={m}>{m === 'al' ? 'Aluminyum' : m === 'cu' ? 'Bakir' : m}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="lv_material">AG Malzeme</label>
            <select
              id="lv_material"
              name="lv_material"
              value={formData.lv_material}
              onChange={handleChange}
            >
              <option value="">Hepsi</option>
              {stats?.materials?.lv?.map(m => (
                <option key={m} value={m}>{m === 'al' ? 'Aluminyum' : m === 'cu' ? 'Bakir' : m}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Elektriksel Parametreler</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="impedance_percent">Empedans / Ucc (%)</label>
            <input
              type="number"
              id="impedance_percent"
              name="impedance_percent"
              value={formData.impedance_percent}
              onChange={handleChange}
              placeholder="ornek: 6"
              min="0"
              max="100"
              step="0.1"
            />
          </div>
          <div className="form-group">
            <label htmlFor="max_no_load_loss_w">Max Bosta Kayip (W)</label>
            <input
              type="number"
              id="max_no_load_loss_w"
              name="max_no_load_loss_w"
              value={formData.max_no_load_loss_w}
              onChange={handleChange}
              placeholder="ornek: 1500"
              min="0"
              step="any"
            />
          </div>
          <div className="form-group">
            <label htmlFor="max_load_loss_w">Max Yuk Kaybi (W)</label>
            <input
              type="number"
              id="max_load_loss_w"
              name="max_load_loss_w"
              value={formData.max_load_loss_w}
              onChange={handleChange}
              placeholder="ornek: 10000"
              min="0"
              step="any"
            />
          </div>
          <div className="form-group">
            <label htmlFor="max_results">Sonuc Sayisi</label>
            <select
              id="max_results"
              name="max_results"
              value={formData.max_results}
              onChange={handleChange}
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button
          type="button"
          className="btn-clear"
          onClick={handleClear}
          disabled={!hasAnyValue}
        >
          Temizle
        </button>
        <button
          type="submit"
          className="btn-search"
          disabled={isLoading || !hasAnyValue}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span>
              Araniyor...
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
              </svg>
              Ara
            </>
          )}
        </button>
      </div>

      {stats && (
        <div className="form-stats">
          <span>{stats.total_designs} dizayn mevcut</span>
          <span>Guc: {stats.rating_range?.min} - {stats.rating_range?.max} kVA</span>
        </div>
      )}
    </form>
  )
}

export default SearchForm

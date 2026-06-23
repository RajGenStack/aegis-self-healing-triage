import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Search, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  ShieldAlert, 
  Heart, 
  Thermometer, 
  TrendingUp, 
  Clock, 
  User, 
  UserX,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';

const API_URL = 'https://olrigx3qm4jqtffx4ejd7tiqmi0mbann.lambda-url.us-east-1.on.aws/';

// High-quality mock data for fallback/offline display
const MOCK_PATIENTS = [
  {
    patient_id: "PAT-002",
    name: "Aditi Patel",
    profile: "CRITICAL",
    timestamp: Math.floor(Date.now() / 1000) - 10,
    vitals: {
      respiration_rate: 26,
      spo2: 90,
      spo2_scale: 1,
      supplemental_oxygen: true,
      systolic_bp: 85,
      heart_rate: 135,
      temperature: 39.5,
      consciousness: "Confused"
    },
    news2_score: 19,
    risk_level: "HIGH",
    score_breakdown: {
      respiration_rate: 3,
      spo2: 3,
      supplemental_oxygen: 2,
      systolic_bp: 3,
      heart_rate: 3,
      temperature: 2,
      consciousness: 3
    }
  },
  {
    patient_id: "PAT-005",
    name: "Aarav Sharma",
    profile: "DETERIORATING",
    timestamp: Math.floor(Date.now() / 1000) - 25,
    vitals: {
      respiration_rate: 22,
      spo2: 93,
      spo2_scale: 1,
      supplemental_oxygen: true,
      systolic_bp: 105,
      heart_rate: 105,
      temperature: 38.4,
      consciousness: "Alert"
    },
    news2_score: 7,
    risk_level: "HIGH",
    score_breakdown: {
      respiration_rate: 2,
      spo2: 2,
      supplemental_oxygen: 2,
      systolic_bp: 1,
      heart_rate: 0,
      temperature: 0,
      consciousness: 0
    }
  },
  {
    patient_id: "PAT-004",
    name: "Priya Singh",
    profile: "RECOVERING",
    timestamp: Math.floor(Date.now() / 1000) - 40,
    vitals: {
      respiration_rate: 16,
      spo2: 95,
      spo2_scale: 1,
      supplemental_oxygen: true,
      systolic_bp: 115,
      heart_rate: 92,
      temperature: 37.1,
      consciousness: "Alert"
    },
    news2_score: 5,
    risk_level: "MEDIUM",
    score_breakdown: {
      respiration_rate: 0,
      spo2: 1,
      supplemental_oxygen: 2,
      systolic_bp: 0,
      heart_rate: 1,
      temperature: 0,
      consciousness: 0
    }
  },
  {
    patient_id: "PAT-001",
    name: "Rohan Gupta",
    profile: "STABLE",
    timestamp: Math.floor(Date.now() / 1000) - 60,
    vitals: {
      respiration_rate: 14,
      spo2: 98,
      spo2_scale: 1,
      supplemental_oxygen: false,
      systolic_bp: 120,
      heart_rate: 72,
      temperature: 36.6,
      consciousness: "Alert"
    },
    news2_score: 0,
    risk_level: "LOW",
    score_breakdown: {
      respiration_rate: 0,
      spo2: 0,
      supplemental_oxygen: 0,
      systolic_bp: 0,
      heart_rate: 0,
      temperature: 0,
      consciousness: 0
    }
  },
  {
    patient_id: "PAT-003",
    name: "Vikram Mehta",
    profile: "STABLE",
    timestamp: Math.floor(Date.now() / 1000) - 75,
    vitals: {
      respiration_rate: 13,
      spo2: 97,
      spo2_scale: 2,
      supplemental_oxygen: false,
      systolic_bp: 118,
      heart_rate: 68,
      temperature: 36.8,
      consciousness: "Alert"
    },
    news2_score: 0,
    risk_level: "LOW",
    score_breakdown: {
      respiration_rate: 0,
      spo2: 0,
      supplemental_oxygen: 0,
      systolic_bp: 0,
      heart_rate: 0,
      temperature: 0,
      consciousness: 0
    }
  }
];

const getFriendlyProfile = (profile) => {
  const mapping = {
    'CRITICAL': 'Needs Urgent Care',
    'DETERIORATING': 'Under Observation',
    'RECOVERING': 'Stable / Improving',
    'STABLE': 'Healthy / Stable'
  };
  return mapping[profile] || profile;
};

function App() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isOffline, setIsOffline] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [expandedCard, setExpandedCard] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Advanced States
  const [acknowledgedPatients, setAcknowledgedPatients] = useState(new Set());
  const [patientHistory, setPatientHistory] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [activeTabMap, setActiveTabMap] = useState({});

  const pollingRef = useRef(null);
  const prevPatientsRef = useRef([]);

  // Helper to add alert notification toasts
  const addNotification = (name, text) => {
    const id = Date.now() + Math.random().toString(36).substr(2, 5);
    setNotifications(prev => [{ id, name, text, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 3));
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 6000);
  };

  // Side-effect handler for patient state changes: tracks history & checks escalations
  useEffect(() => {
    if (patients.length === 0) return;

    // 1. Check for clinical score deterioration (escalation)
    const prevMap = {};
    prevPatientsRef.current.forEach(p => {
      prevMap[p.patient_id] = p;
    });

    patients.forEach(patient => {
      const pid = patient.patient_id;
      const prev = prevMap[pid];
      if (patient.risk_level === 'HIGH' && (!prev || prev.risk_level !== 'HIGH')) {
        addNotification(patient.name, `Alert status deteriorated to URGENT CARE (Score: ${patient.news2_score})`);
      }
    });

    // 2. Maintain up to 5 readings in history per patient
    setPatientHistory(prevHistory => {
      const updated = { ...prevHistory };
      let changed = false;

      patients.forEach(patient => {
        const pid = patient.patient_id;
        const currentList = updated[pid] || [];
        if (currentList.length === 0 || currentList[0].timestamp !== patient.timestamp) {
          updated[pid] = [
            {
              timestamp: patient.timestamp,
              news2_score: patient.news2_score,
              risk_level: patient.risk_level,
              vitals: { ...patient.vitals }
            },
            ...currentList
          ].slice(0, 5);
          changed = true;
        }
      });

      return changed ? updated : prevHistory;
    });

    // Keep ref updated
    prevPatientsRef.current = patients;
  }, [patients]);

  // Fetch telemetry updates
  const fetchTriageData = async (silent = false) => {
    if (!silent) setLoading(true);
    setIsRefreshing(true);
    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const sortedData = [...data].sort((a, b) => b.news2_score - a.news2_score);
      
      setPatients(sortedData);
      setIsOffline(false);
      setError(null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.warn("API offline, falling back to mock clinical data.", err);
      const data = MOCK_PATIENTS;
      const sortedData = [...data].sort((a, b) => b.news2_score - a.news2_score);
      
      setPatients(sortedData);
      setIsOffline(true);
      setError("Active telemetry pipeline offline. Displaying fallback simulated data.");
      setLastUpdated(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTriageData();
  }, []);

  // Polling loop management
  useEffect(() => {
    if (autoRefresh) {
      pollingRef.current = setInterval(() => {
        fetchTriageData(true);
      }, 4000);
    } else {
      if (pollingRef.current) clearInterval(pollingRef.current);
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [autoRefresh]);

  // Handle manual trigger
  const handleManualRefresh = () => {
    fetchTriageData(false);
  };

  // Toggle alert acknowledgment
  const toggleAcknowledge = (patientId, patientName) => {
    setAcknowledgedPatients(prev => {
      const copy = new Set(prev);
      if (copy.has(patientId)) {
        copy.delete(patientId);
        addNotification(patientName, `Triage alert changed back to active.`);
      } else {
        copy.add(patientId);
        addNotification(patientName, `Alert acknowledged. Responding medical staff notified.`);
      }
      return copy;
    });
  };

  // Get trend arrow indicator
  const getTrendIndicator = (patientId, currentScore) => {
    const history = patientHistory[patientId];
    if (!history || history.length < 2) return { icon: '▶', text: 'Stable', class: 'trend-stable' };
    const prevScore = history[1].news2_score;
    if (currentScore > prevScore) {
      return { icon: '▲', text: 'Worsening', class: 'trend-worsening' };
    } else if (currentScore < prevScore) {
      return { icon: '▼', text: 'Improving', class: 'trend-improving' };
    }
    return { icon: '▶', text: 'Stable', class: 'trend-stable' };
  };

  // Trigger Critical Event (client-side simulation)
  const triggerCriticalEvent = () => {
    if (patients.length === 0) return;
    const updated = [...patients];
    
    const nonCriticalIdxs = updated.map((p, i) => p.news2_score < 7 ? i : -1).filter(idx => idx !== -1);
    const targetIdx = nonCriticalIdxs.length > 0 
      ? nonCriticalIdxs[Math.floor(Math.random() * nonCriticalIdxs.length)]
      : Math.floor(Math.random() * updated.length);
      
    const target = { ...updated[targetIdx] };
    target.timestamp = Math.floor(Date.now() / 1000);
    target.vitals = {
      respiration_rate: 28,
      spo2: 83,
      spo2_scale: 1,
      supplemental_oxygen: true,
      systolic_bp: 72,
      heart_rate: 145,
      temperature: 39.8,
      consciousness: "Confused"
    };
    target.news2_score = 17;
    target.risk_level = "HIGH";
    target.score_breakdown = {
      respiration_rate: 3,
      spo2: 3,
      supplemental_oxygen: 2,
      systolic_bp: 3,
      heart_rate: 3,
      temperature: 2,
      consciousness: 3
    };
    
    updated[targetIdx] = target;
    
    addNotification(target.name, `CRITICAL: Vital signs deteriorated rapidly (Alert Score: 17)`);
    
    setPatients(updated.sort((a, b) => (b.news2_score - a.news2_score)));
    
    setAcknowledgedPatients(prev => {
      const copy = new Set(prev);
      copy.delete(target.patient_id);
      return copy;
    });
  };

  // Trigger Recovery Event (client-side simulation)
  const triggerRecoveryEvent = () => {
    const criticalPatients = patients.filter(p => p.risk_level === 'HIGH');
    if (criticalPatients.length === 0) {
      addNotification("System", "No critical patients found to recover.");
      return;
    }
    
    const targetPatient = criticalPatients[Math.floor(Math.random() * criticalPatients.length)];
    const updated = patients.map(p => {
      if (p.patient_id === targetPatient.patient_id) {
        const recovered = { ...p };
        recovered.timestamp = Math.floor(Date.now() / 1000);
        recovered.vitals = {
          respiration_rate: 14,
          spo2: 98,
          spo2_scale: 1,
          supplemental_oxygen: false,
          systolic_bp: 120,
          heart_rate: 72,
          temperature: 36.6,
          consciousness: "Alert"
        };
        recovered.news2_score = 0;
        recovered.risk_level = "LOW";
        recovered.score_breakdown = {
          respiration_rate: 0,
          spo2: 0,
          supplemental_oxygen: 0,
          systolic_bp: 0,
          heart_rate: 0,
          temperature: 0,
          consciousness: 0
        };
        addNotification(recovered.name, `RECOVERY: Patient stabilized. Vitals returned to normal.`);
        return recovered;
      }
      return p;
    });
    
    setPatients(updated.sort((a, b) => (b.news2_score - a.news2_score)));
    
    setAcknowledgedPatients(prev => {
      const copy = new Set(prev);
      copy.delete(targetPatient.patient_id);
      return copy;
    });
  };

  // Reset Demo Data (client-side simulation)
  const resetDemoData = () => {
    const baseline = MOCK_PATIENTS.map(p => ({
      ...p,
      timestamp: Math.floor(Date.now() / 1000)
    })).sort((a, b) => b.news2_score - a.news2_score);
    
    setPatients(baseline);
    setAcknowledgedPatients(new Set());
    setPatientHistory({});
    addNotification("System", "Dashboard demo data reset to default baseline.");
  };

  // Filter and search computation
  const filteredPatients = patients.filter(patient => {
    const matchesSearch = 
      patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.patient_id.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (statusFilter === 'ALL') return matchesSearch;
    return matchesSearch && patient.risk_level === statusFilter;
  });

  // KPI Calculations
  const totalMonitored = patients.length;
  const highRiskCount = patients.filter(p => p.risk_level === 'HIGH').length;
  const mediumRiskCount = patients.filter(p => p.risk_level === 'MEDIUM').length;
  const lowRiskCount = patients.filter(p => p.risk_level === 'LOW').length;  return (
    <div className="dashboard-container">
      {/* Toast Notifications */}
      <div className="toast-container">
        {notifications.map(n => (
          <div key={n.id} className="toast-item">
            <div className="toast-item-header">
              <span className="toast-item-name">{n.name}</span>
              <span className="toast-item-time">{n.time}</span>
            </div>
            <p className="toast-item-text">{n.text}</p>
          </div>
        ))}
      </div>

      {/* -----------------------------------------------------------------------------
       * High-tech Navigation / Header
       * ----------------------------------------------------------------------------- */}
      <header className="dashboard-header">
        <div className="header-container">
          <div className="brand-section">
            <div className="brand-logo-wrapper">
              <Activity className="h-6 w-6 text-rose-500 animate-pulse" />
            </div>
            <div>
              <h1 className="brand-title">
                AEGIS <span>Patient Health Dashboard</span>
              </h1>
              <p className="brand-subtitle">Simple & Easy Real-Time Health Monitor</p>
            </div>
          </div>

          <div className="controls-section">
            {/* Status Indicator */}
            <div className="status-pill">
              <span className={isOffline ? "pulse-indicator-red" : "pulse-indicator"}></span>
              <span>
                {isOffline ? "Offline Mode (Simulated Data)" : "Live Pipeline Connected"}
              </span>
            </div>

            {/* Auto Refresh Toggle */}
            <div className="toggle-wrapper">
              <span className="toggle-label">Auto-Refresh (4s)</span>
              <button 
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`toggle-btn ${autoRefresh ? 'active' : 'inactive'}`}
              >
                <span className={`toggle-circle ${autoRefresh ? 'active' : 'inactive'}`} />
              </button>
            </div>

            {/* Refresh Button */}
            <button 
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="refresh-btn"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-rose-500' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Connection Offline Warning Banner */}
        {error && (
          <div className="warning-banner">
            <Info className="h-5 w-5 text-amber-500 shrink-0 warning-banner-icon" />
            <div>
              <p className="warning-title">Telemetry Ingestion Warning</p>
              <p className="warning-desc">{error}</p>
            </div>
          </div>
        )}

        {/* Demo Simulation Control Panel */}
        <section className="simulation-control-panel">
          <div className="simulation-panel-title-wrapper">
            <h3 className="simulation-panel-title">Demo Simulation Console</h3>
            <p className="simulation-panel-subtitle">Trigger rapid clinical events to test dashboard responsiveness & automatic list sorting</p>
          </div>
          <div className="simulation-buttons">
            <button className="simulation-btn simulation-btn-critical" onClick={triggerCriticalEvent}>
              Trigger Critical Event
            </button>
            <button className="simulation-btn simulation-btn-recover" onClick={triggerRecoveryEvent}>
              Trigger Recovery
            </button>
            <button className="simulation-btn" onClick={resetDemoData}>
              Reset Demo Data
            </button>
          </div>
        </section>

        {/* -----------------------------------------------------------------------------
         * KPI Metrics Grid
         * ----------------------------------------------------------------------------- */}
        <section className="kpi-grid">
          <div className="kpi-card">
            <div>
              <p className="kpi-label">Monitored Patients</p>
              <h3 className="kpi-value">
                {loading ? "..." : totalMonitored}
              </h3>
            </div>
            <div className="kpi-icon-wrapper">
              <User className="h-5 w-5" />
            </div>
          </div>

          <div className="kpi-card">
            <div>
              <p className="kpi-label">Urgent Care Needed</p>
              <h3 className="kpi-value text-color-high">
                {loading ? "..." : highRiskCount}
              </h3>
            </div>
            <div className={`kpi-icon-wrapper ${highRiskCount > 0 ? 'active-red' : ''}`}>
              <ShieldAlert className="h-5 w-5" />
            </div>
          </div>

          <div className="kpi-card">
            <div>
              <p className="kpi-label">Watch List / Attention</p>
              <h3 className="kpi-value text-color-medium">
                {loading ? "..." : mediumRiskCount}
              </h3>
            </div>
            <div className={`kpi-icon-wrapper ${mediumRiskCount > 0 ? 'active-amber' : ''}`}>
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>

          <div className="kpi-card">
            <div>
              <p className="kpi-label">Healthy / Stable</p>
              <h3 className="kpi-value text-color-low">
                {loading ? "..." : lowRiskCount}
              </h3>
            </div>
            <div className="kpi-icon-wrapper active-green">
              <CheckCircle className="h-5 w-5" />
            </div>
          </div>
        </section>

        {/* -----------------------------------------------------------------------------
         * Filters & Search
         * ----------------------------------------------------------------------------- */}
        <section className="filter-bar">
          {/* Search Box */}
          <div className="search-box">
            <Search className="search-icon" size={18} />
            <input 
              type="text" 
              placeholder="Search by patient ID or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          {/* Filtering Tabs */}
          <div className="filter-tabs">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((filter) => (
              <button
                key={filter}
                onClick={() => setStatusFilter(filter)}
                className={`filter-tab-btn ${statusFilter === filter ? 'active' : ''}`}
              >
                {filter === 'ALL' ? 'Show All' : filter === 'HIGH' ? 'Urgent Care' : filter === 'MEDIUM' ? 'Watch List' : 'Stable'}
              </button>
            ))}
          </div>
        </section>

        {/* -----------------------------------------------------------------------------
         * Monitored Patient Grid List
         * ----------------------------------------------------------------------------- */}
        <section className="queue-list">
          <div className="queue-header-row">
            <h2 className="queue-title">
              Patients List ({filteredPatients.length} Patients)
            </h2>
            {lastUpdated && (
              <div className="last-updated-text">
                <Clock className="h-3.5 w-3.5" />
                <span>Last updated: {lastUpdated}</span>
              </div>
            )}
          </div>

          {loading ? (
            /* Loading State */
            <div className="skeletons-wrapper">
              {[1, 2, 3].map(i => (
                <div key={i} className="skeleton skeleton-item" />
              ))}
            </div>
          ) : filteredPatients.length === 0 ? (
            /* Empty State */
            <div className="empty-state">
              <UserX className="empty-icon" size={40} />
              <p className="empty-title">No matching patient records found</p>
              <p className="empty-desc">Try adjusting your filters or checking the vitals generator.</p>
            </div>
          ) : (
            /* Patient Grid */
            <div className="queue-list">
              {filteredPatients.map((patient) => {
                const isExpanded = expandedCard === patient.patient_id;
                const hasEscalationTrigger = Object.values(patient.score_breakdown || {}).includes(3);
                const isAcked = acknowledgedPatients.has(patient.patient_id);
                const borderClass = isAcked 
                  ? 'border-acknowledged' 
                  : (patient.risk_level === 'HIGH' ? 'border-high' : patient.risk_level === 'MEDIUM' ? 'border-medium' : 'border-low');
                const trend = getTrendIndicator(patient.patient_id, patient.news2_score);
                const currentTab = activeTabMap[patient.patient_id] || 'breakdown';
                const history = patientHistory[patient.patient_id] || [];

                return (
                  <div 
                    key={patient.patient_id}
                    className={`glass-panel ${borderClass}`}
                  >
                    {/* Header Row */}
                    <div 
                      onClick={() => setExpandedCard(isExpanded ? null : patient.patient_id)}
                      className="patient-card-header"
                    >
                      <div className="patient-left-group">
                        {/* Status Pulse Ring */}
                        <div className="patient-status-indicator">
                          {isAcked ? (
                            <span className="indicator-acknowledged" />
                          ) : (
                            <>
                              {patient.risk_level === 'HIGH' && <span className="pulse-indicator-red" />}
                              {patient.risk_level === 'MEDIUM' && <span className="pulse-indicator-amber" />}
                              {patient.risk_level === 'LOW' && <span className="pulse-indicator" />}
                            </>
                          )}
                        </div>

                        {/* Identification */}
                        <div className="patient-ident">
                          <div className="patient-title-row">
                            <h3 className="patient-name">{patient.name}</h3>
                            <span className={`trend-pill ${trend.class}`} title={`NEWS2 Trend: ${trend.text}`}>
                              {trend.icon} {trend.text}
                            </span>
                            <span className="patient-id-badge">
                              ID: {patient.patient_id}
                            </span>
                            {hasEscalationTrigger && !isAcked && (
                              <span className="escalation-badge">
                                <AlertTriangle size={12} /> ATTENTION REQUIRED
                              </span>
                            )}
                          </div>
                          
                          <div className="patient-meta">
                            <span>Status: <strong>{isAcked ? 'Staff Attending' : getFriendlyProfile(patient.profile)}</strong></span>
                            <span>•</span>
                            <span className="last-updated-text"><Clock size={12} /> Checked at {new Date(patient.timestamp * 1000).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Vital Statistics Row Preview */}
                      <div className="vitals-preview-bar">
                        <div className="vitals-preview-item">
                          <span className="vitals-preview-label">Heart Rate</span>
                          <span className="vitals-preview-value">{patient.vitals.heart_rate} bpm</span>
                        </div>
                        <div className="vitals-preview-divider" />
                        <div className="vitals-preview-item">
                          <span className="vitals-preview-label">Oxygen Level</span>
                          <span className="vitals-preview-value">{patient.vitals.spo2}%</span>
                        </div>
                        <div className="vitals-preview-divider" />
                        <div className="vitals-preview-item">
                          <span className="vitals-preview-label">Blood Pressure</span>
                          <span className="vitals-preview-value">{patient.vitals.systolic_bp} mmHg</span>
                        </div>
                        <div className="vitals-preview-divider" />
                        <div className="vitals-preview-item">
                          <span className="vitals-preview-label">Temperature</span>
                          <span className="vitals-preview-value">{patient.vitals.temperature}°C</span>
                        </div>
                      </div>

                      {/* Score Gauge & Action */}
                      <div className="card-right-group" onClick={(e) => e.stopPropagation()}>
                        {(patient.risk_level === 'HIGH' || patient.risk_level === 'MEDIUM') && (
                          <button 
                            className={`ack-btn ${isAcked ? 'acknowledged' : ''}`}
                            onClick={() => toggleAcknowledge(patient.patient_id, patient.name)}
                          >
                            {isAcked ? (
                              <>
                                <CheckCircle size={12} /> Attended
                              </>
                            ) : (
                              'Acknowledge'
                            )}
                          </button>
                        )}
                        <div className="news2-score-badge-wrapper" onClick={() => setExpandedCard(isExpanded ? null : patient.patient_id)}>
                          <span className="news2-score-label">Alert Score</span>
                          <span className={`news2-score-badge ${
                            patient.news2_score >= 7 ? 'badge-news-critical' : patient.news2_score >= 5 ? 'badge-news-warning' : 'badge-news-stable'
                          }`}>
                            {patient.news2_score}
                          </span>
                        </div>

                        <div className="expand-icon-wrapper" onClick={() => setExpandedCard(isExpanded ? null : patient.patient_id)}>
                          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </div>
                      </div>
                    </div>

                    {/* Detailed Accordion Section */}
                    {isExpanded && (
                      <div className="card-details-section">
                        <h4 className="details-title">
                          <Info size={14} /> Health Alert Summary & Logs
                        </h4>

                        {/* Details Tab Switcher */}
                        <div className="details-tab-bar">
                          <button 
                            className={`details-tab-btn ${currentTab === 'breakdown' ? 'active' : ''}`}
                            onClick={() => setActiveTabMap(prev => ({ ...prev, [patient.patient_id]: 'breakdown' }))}
                          >
                            Alert Breakdown
                          </button>
                          <button 
                            className={`details-tab-btn ${currentTab === 'history' ? 'active' : ''}`}
                            onClick={() => setActiveTabMap(prev => ({ ...prev, [patient.patient_id]: 'history' }))}
                          >
                            Vitals History Log
                          </button>
                        </div>

                        {currentTab === 'breakdown' ? (
                          <div className="details-summary-content">
                            <p className="summary-text">
                              <strong>Care Recommendation:</strong> {
                                isAcked
                                  ? 'Staff attending. Awaiting further clinical review.'
                                  : patient.risk_level === 'HIGH' 
                                  ? 'Needs urgent clinical attention. Please alert the attending doctor immediately.' 
                                  : patient.risk_level === 'MEDIUM' 
                                  ? 'Needs close observation. Monitor vitals hourly.' 
                                  : 'Patient is stable. Continue standard routine checks.'
                              }
                            </p>
                            
                            <div className="alert-bullets">
                              {Object.entries(patient.score_breakdown || {}).map(([param, score]) => {
                                if (score > 0) {
                                  let label = param.replace(/_/g, ' ');
                                  label = label.charAt(0).toUpperCase() + label.slice(1);
                                  if (param === 'spo2') label = 'Oxygen level (SpO2)';
                                  if (param === 'systolic_bp') label = 'Blood pressure';
                                  if (param === 'heart_rate') label = 'Heart rate';
                                  if (param === 'respiration_rate') label = 'Breathing rate';
                                  if (param === 'consciousness') label = 'Consciousness level';
                                  if (param === 'supplemental_oxygen') label = 'On supplemental oxygen';
                                  
                                  let val = patient.vitals[param];
                                  if (param === 'supplemental_oxygen') val = val ? 'Yes' : 'No';
                                  
                                  const alertClass = score === 3 ? 'high-alert' : 'medium-alert';
                                  
                                  return (
                                    <div key={param} className={`alert-bullet-item ${alertClass}`}>
                                      <AlertTriangle size={14} />
                                      <span><strong>{label}:</strong> Checked as irregular (Value: {val})</span>
                                    </div>
                                  );
                                }
                                return null;
                              })}
                              {Object.values(patient.score_breakdown || {}).reduce((a, b) => a + b, 0) === 0 && (
                                <div className="alert-bullet-item low-alert">
                                  <CheckCircle size={14} />
                                  <span>All vital signs are in the healthy range.</span>
                                </div>
                              )}
                            </div>

                            <div className="details-quick-vitals">
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">Breathing Rate</span>
                                <span className="quick-vital-val">{patient.vitals.respiration_rate} bpm</span>
                              </div>
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">Oxygen Level</span>
                                <span className="quick-vital-val">{patient.vitals.spo2}% {patient.vitals.spo2_scale === 2 ? '(COPD)' : ''}</span>
                              </div>
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">On Oxygen?</span>
                                <span className="quick-vital-val">{patient.vitals.supplemental_oxygen ? 'Yes' : 'No'}</span>
                              </div>
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">Blood Pressure</span>
                                <span className="quick-vital-val">{patient.vitals.systolic_bp} mmHg</span>
                              </div>
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">Heart Rate</span>
                                <span className="quick-vital-val">{patient.vitals.heart_rate} bpm</span>
                              </div>
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">Body Temp</span>
                                <span className="quick-vital-val">{patient.vitals.temperature}°C</span>
                              </div>
                              <div className="quick-vital-box">
                                <span className="quick-vital-label">Consciousness</span>
                                <span className="quick-vital-val">{patient.vitals.consciousness}</span>
                              </div>
                              <div className="quick-vital-box highlight-triage">
                                <span className="quick-vital-label">Triage Level</span>
                                <span className={`quick-vital-val ${
                                  patient.risk_level === 'HIGH' ? 'text-color-high' : patient.risk_level === 'MEDIUM' ? 'text-color-medium' : 'text-color-low'
                                }`}>{patient.risk_level} RISK</span>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="details-history-content">
                            {history.length === 0 ? (
                              <p className="summary-text">No vitals history logs captured yet.</p>
                            ) : (
                              <div className="history-table-wrapper">
                                <table className="history-table">
                                  <thead>
                                    <tr>
                                      <th>Time</th>
                                      <th>NEWS2</th>
                                      <th>Risk Level</th>
                                      <th>Resp Rate</th>
                                      <th>SpO2</th>
                                      <th>Systolic BP</th>
                                      <th>Heart Rate</th>
                                      <th>Temp</th>
                                      <th>Oxygen Source</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {history.map((h, idx) => (
                                      <tr key={idx}>
                                        <td>{new Date(h.timestamp * 1000).toLocaleTimeString()}</td>
                                        <td><strong>{h.news2_score}</strong></td>
                                        <td>
                                          <span className={`quick-vital-val ${
                                            h.risk_level === 'HIGH' ? 'text-color-high' : h.risk_level === 'MEDIUM' ? 'text-color-medium' : 'text-color-low'
                                          }`}>
                                            {h.risk_level}
                                          </span>
                                        </td>
                                        <td>{h.vitals.respiration_rate} bpm</td>
                                        <td>{h.vitals.spo2}%</td>
                                        <td>{h.vitals.systolic_bp} mmHg</td>
                                        <td>{h.vitals.heart_rate} bpm</td>
                                        <td>{h.vitals.temperature}°C</td>
                                        <td>{h.vitals.supplemental_oxygen ? 'On Supplemental' : 'Room Air'}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {/* -----------------------------------------------------------------------------
       * High-tech Dashboard Footer
       * ----------------------------------------------------------------------------- */}
      <footer className="dashboard-footer">
        <div className="footer-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <span className="footer-link-item"><span className="footer-dot-green"></span> AWS Ingestion Active</span>
            <span className="footer-link-item"><span className="footer-dot-green"></span> Live Telemetry Connected</span>
          </div>
          <p className="footer-text" style={{ margin: 0, textAlign: 'center' }}>
            © 2026 <strong>Rajan Kumar</strong>. All rights reserved. Standard clinical Early Warning Scoring (NEWS2).
          </p>
          <div className="footer-socials" style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '2px' }}>
            <a href="https://github.com/RajGenStack" target="_blank" rel="noopener noreferrer" style={{ color: '#64748b', textDecoration: 'none', transition: 'color 0.2s' }} onMouseOver={(e) => e.target.style.color = '#e11d48'} onMouseOut={(e) => e.target.style.color = '#64748b'}>GitHub</a>
            <span style={{ color: '#cbd5e1' }}>•</span>
            <a href="https://www.linkedin.com/in/rajan-kumar42" target="_blank" rel="noopener noreferrer" style={{ color: '#64748b', textDecoration: 'none', transition: 'color 0.2s' }} onMouseOver={(e) => e.target.style.color = '#e11d48'} onMouseOut={(e) => e.target.style.color = '#64748b'}>LinkedIn</a>
            <span style={{ color: '#cbd5e1' }}>•</span>
            <a href="https://www.instagram.com/rajansxarma?igsh=eDh1bnk1NmVsZjcz" target="_blank" rel="noopener noreferrer" style={{ color: '#64748b', textDecoration: 'none', transition: 'color 0.2s' }} onMouseOver={(e) => e.target.style.color = '#e11d48'} onMouseOut={(e) => e.target.style.color = '#64748b'}>Instagram</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

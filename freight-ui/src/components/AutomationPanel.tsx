import React, { useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE } from '../config';
import { useI18n } from '../i18n';

type JobType = 'one_pipeline' | 'hapag_pipeline';

interface AutomationPanelProps {
  onWorkflowComplete?: (jobType: JobType, success: boolean) => void;
}

interface JobStatus {
  jobId: string | null;
  jobType: JobType | null;
  status: 'idle' | 'running' | 'completed' | 'failed' | string;
  isRunning: boolean;
  startedAt: string | null;
  endedAt: string | null;
  exitCode: number | null;
  command: string[] | null;
  nextLogIndex: number;
}

interface JobLog {
  index: number;
  timestamp: string;
  message: string;
}

interface ProgressModel {
  percent: number;
  title: string;
  subtitle: string;
  tone: 'idle' | 'running' | 'success' | 'error';
}

const POLL_INTERVAL_MS = 1200;
type TranslateFn = (key: any, params?: Record<string, string | number>) => string;

const clampPercent = (value: number): number => {
  if (Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
};

const hasText = (value: string, target: string): boolean =>
  value.toLowerCase().includes(target.toLowerCase());

function getOnePipelineProgress(status: JobStatus, logs: JobLog[], t: TranslateFn): ProgressModel {
  let step = 1;
  let step1Total = 0;
  const step1Done = new Set<string>();

  let step2Total = 0;
  let step2Current = 0;

  let step3Score = 0;

  for (const log of logs) {
    const message = log.message;

    if (hasText(message, 'Step 2/3')) step = 2;
    if (hasText(message, 'Step 3/3')) step = 3;

    const step1TotalMatch = message.match(/Processing\s+(\d+)\s+destination\(s\)/i);
    if (step1TotalMatch && step1Total === 0) {
      step1Total = Number(step1TotalMatch[1]);
    }

    const step1DoneMatch = message.match(/\[WORKER\s+\d+\]\s+\[(SUCCESS|FAILED)\]\s+(.+)$/i);
    if (step1DoneMatch) {
      step1Done.add(step1DoneMatch[2].trim());
    }

    const step2TotalMatch = message.match(/DESTINATIONS:\s*(\d+)/i);
    if (step2TotalMatch) {
      step2Total = Number(step2TotalMatch[1]);
    }

    const step2CurrentMatch = message.match(/\[(\d+)\/(\d+)\]\s+Processing\s+/i);
    if (step2CurrentMatch) {
      step2Current = Math.max(step2Current, Number(step2CurrentMatch[1]));
      step2Total = Math.max(step2Total, Number(step2CurrentMatch[2]));
    }

    if (hasText(message, 'Loading inland rates')) step3Score = Math.max(step3Score, 20);
    if (hasText(message, 'Adding ocean rates')) step3Score = Math.max(step3Score, 45);
    if (hasText(message, 'Calculating total rates')) step3Score = Math.max(step3Score, 65);
    if (hasText(message, 'Adding cost rankings')) step3Score = Math.max(step3Score, 80);
    if (hasText(message, 'Saving processed data')) step3Score = Math.max(step3Score, 95);
    if (hasText(message, 'Processing complete!')) step3Score = Math.max(step3Score, 100);
  }

  if (status.status === 'completed' && status.exitCode === 0) {
    return {
      percent: 100,
      title: t('progressOneCompletedTitle'),
      subtitle: t('progressOneCompletedSubtitle'),
      tone: 'success',
    };
  }

  if (status.status === 'failed') {
    return {
      percent: clampPercent(step === 1 ? 18 : step === 2 ? 56 : 88),
      title: t('progressOneStoppedTitle'),
      subtitle: t('progressOneStoppedSubtitle'),
      tone: 'error',
    };
  }

  if (step <= 1) {
    const progress = step1Total > 0 ? step1Done.size / step1Total : 0.15;
    return {
      percent: clampPercent(5 + progress * 30),
      title: t('progressPreparingDestinationsTitle'),
      subtitle: step1Total > 0
        ? t('progressDestinationsValidatedSubtitle', { done: step1Done.size, total: step1Total })
        : t('progressPreparingDestinationsSubtitle'),
      tone: 'running',
    };
  }

  if (step === 2) {
    const progress = step2Total > 0 ? step2Current / step2Total : 0.15;
    return {
      percent: clampPercent(35 + progress * 45),
      title: t('progressCollectingOneTitle'),
      subtitle: step2Total > 0
        ? t('progressDestinationsScrapedSubtitle', { done: Math.min(step2Current, step2Total), total: step2Total })
        : t('progressCollectingOneSubtitle'),
      tone: 'running',
    };
  }

  return {
    percent: clampPercent(80 + (step3Score / 100) * 20),
    title: t('progressFinalizingTitle'),
    subtitle: t('progressFinalizingSubtitle'),
    tone: 'running',
  };
}

function getHapagPipelineProgress(status: JobStatus, logs: JobLog[], t: TranslateFn): ProgressModel {
  let total = 0;
  let current = 0;

  for (const log of logs) {
    const message = log.message;

    const totalMatch = message.match(/Processing\s+(\d+)\s+destinations/i);
    if (totalMatch) {
      total = Number(totalMatch[1]);
    }

    const currentMatch = message.match(/Processing\s+(\d+)\/(\d+):/i);
    if (currentMatch) {
      current = Math.max(current, Number(currentMatch[1]));
      total = Math.max(total, Number(currentMatch[2]));
    }
  }

  if (status.status === 'completed' && status.exitCode === 0) {
    return {
      percent: 100,
      title: t('progressHapagCompletedTitle'),
      subtitle: t('progressHapagCompletedSubtitle'),
      tone: 'success',
    };
  }

  if (status.status === 'failed') {
    return {
      percent: clampPercent(total > 0 ? 10 + (current / total) * 80 : 40),
      title: t('progressHapagStoppedTitle'),
      subtitle: t('progressHapagStoppedSubtitle'),
      tone: 'error',
    };
  }

  const progress = total > 0 ? current / total : 0.2;
  return {
    percent: clampPercent(10 + progress * 80),
    title: t('progressCollectingHapagTitle'),
    subtitle: total > 0
      ? t('progressDestinationsProcessedSubtitle', { done: Math.min(current, total), total })
      : t('progressPreparingExtractionSubtitle'),
    tone: 'running',
  };
}

function deriveProgress(status: JobStatus | null, logs: JobLog[], t: TranslateFn): ProgressModel {
  if (!status || status.status === 'idle') {
    return {
      percent: 0,
      title: t('progressReadyTitle'),
      subtitle: t('progressReadySubtitle'),
      tone: 'idle',
    };
  }

  if (status.jobType === 'one_pipeline') {
    return getOnePipelineProgress(status, logs, t);
  }

  if (status.jobType === 'hapag_pipeline') {
    return getHapagPipelineProgress(status, logs, t);
  }

  return {
    percent: status.isRunning ? 20 : status.status === 'completed' ? 100 : 0,
    title: status.isRunning ? t('progressWorkflowInProgressTitle') : t('progressReadyTitle'),
    subtitle: status.isRunning
      ? t('progressPreparingWorkflowSubtitle')
      : t('progressReadySubtitle'),
    tone: status.status === 'failed' ? 'error' : status.status === 'completed' ? 'success' : 'idle',
  };
}

const AutomationPanel: React.FC<AutomationPanelProps> = ({ onWorkflowComplete }) => {
  const { t } = useI18n();
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [logs, setLogs] = useState<JobLog[]>([]);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);
  const nextIndexRef = useRef<number>(0);
  const wasRunningRef = useRef<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [urlCheckerInput, setUrlCheckerInput] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [displayPercent, setDisplayPercent] = useState<number>(0);
  const [loadingDotCount, setLoadingDotCount] = useState<number>(0);

  const isRunning = Boolean(status?.isRunning);
  const progress = useMemo(() => deriveProgress(status, logs, t), [status, logs, t]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setDisplayPercent((current) => {
        const target = isRunning ? Math.max(progress.percent, current) : progress.percent;
        if (!isRunning && target >= 100 && status?.status === 'completed') {
          return 100;
        }
        const delta = target - current;

        if (Math.abs(delta) < 0.2) {
          return target;
        }

        const adaptiveStep = Math.max(0.25, Math.abs(delta) * 0.12);
        const next = current + Math.sign(delta) * adaptiveStep;

        if (Math.sign(delta) > 0) {
          return Math.min(next, target);
        }
        return Math.max(next, target);
      });
    }, 70);

    return () => window.clearInterval(interval);
  }, [progress.percent, isRunning, status?.status]);

  useEffect(() => {
    if (!isRunning) {
      setLoadingDotCount(0);
      return;
    }

    const interval = window.setInterval(() => {
      setLoadingDotCount((prev) => (prev + 1) % 4);
    }, 380);

    return () => window.clearInterval(interval);
  }, [isRunning]);

  const fetchStatus = async () => {
    const res = await fetch(`${API_BASE}/jobs/status`);
    if (!res.ok) throw new Error('Failed to fetch job status');
    const data = await res.json();
    setStatus(data);
  };

  const fetchLogs = async () => {
    const res = await fetch(`${API_BASE}/jobs/logs?from=${nextIndexRef.current}&limit=800`);
    if (!res.ok) throw new Error('Failed to fetch job logs');
    const data = await res.json();

    const newLogs: JobLog[] = data.logs || [];
    if (newLogs.length > 0) {
      setLogs((prev) => [...prev, ...newLogs].slice(-3000));
    }
    const next = data.nextLogIndex ?? nextIndexRef.current;
    nextIndexRef.current = next;
  };

  useEffect(() => {
    let cancelled = false;

    const sync = async () => {
      try {
        await fetchStatus();
        await fetchLogs();
      } catch (e) {
        if (!cancelled) {
          setError(t('automationSyncError'));
        }
      }
    };

    sync();
    const timer = window.setInterval(sync, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [t]);

  useEffect(() => {
    const wasRunning = wasRunningRef.current;
    const isRunningNow = Boolean(status?.isRunning);

    if (wasRunning && !isRunningNow && status?.jobType && onWorkflowComplete) {
      const success = status.status === 'completed' && status.exitCode === 0;
      onWorkflowComplete(status.jobType, success);
    }

    wasRunningRef.current = isRunningNow;
  }, [status, onWorkflowComplete]);

  const runJob = async (jobType: JobType) => {
    setLoading(true);
    setError('');
    setShowTechnicalDetails(false);
    setLogs([]);
    nextIndexRef.current = 0;
    setDisplayPercent(0);
    setStatus({
      jobId: null,
      jobType,
      status: 'running',
      isRunning: true,
      startedAt: null,
      endedAt: null,
      exitCode: null,
      command: null,
      nextLogIndex: 0,
    });

    try {
      const payload: { jobType: JobType; destinations?: string[] } = { jobType };
      if (jobType === 'one_pipeline') {
        const destinations = urlCheckerInput
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean);
        if (destinations.length > 0) {
          payload.destinations = destinations;
        }
      }

      const res = await fetch(`${API_BASE}/jobs/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || t('automationStartError'));
      }

      setStatus(data.status);
    } catch (e) {
      setError((e as Error).message || t('automationStartError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card automation-panel">
      <div className="card-header">
        <h2 className="card-title">{t('automationControlTitle')}</h2>
      </div>
      <div className="card-body">
        <p className="automation-status">
          <strong>{t('statusLabel')}:</strong>{' '}
          <span className={`automation-status-text ${isRunning ? 'is-running' : ''}`}>
            {progress.title}
            {isRunning ? '.'.repeat(loadingDotCount) : ''}
          </span>
          {status?.exitCode !== null && status?.exitCode !== undefined && !status.isRunning
            ? ` ${t('statusCode', { code: status.exitCode })}`
            : ''}
        </p>

        <div className={`automation-progress automation-progress--${progress.tone}`}>
          <div className="automation-progress-head">
            <span>{progress.subtitle}</span>
            <span>{clampPercent(displayPercent)}%</span>
          </div>
          <div className="automation-progress-track">
            <div
              className={`automation-progress-fill automation-progress-fill--${progress.tone}`}
              style={{ width: `${clampPercent(displayPercent)}%` }}
            />
          </div>
        </div>

        <div className="automation-input-group">
          <label htmlFor="url-checker-dests">{t('onePipelineDestinationsLabel')}</label>
          <textarea
            id="url-checker-dests"
            value={urlCheckerInput}
            onChange={(e) => setUrlCheckerInput(e.target.value)}
            placeholder={t('onePipelineDestinationsPlaceholder')}
            rows={3}
            disabled={isRunning || loading}
          />
        </div>

        <div className="automation-initiate">
          <button
            type="button"
            className="btn-initiate"
            onClick={() => runJob('one_pipeline')}
            disabled={isRunning || loading}
          >
            {t('initiateOneWorkflow')}
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={() => runJob('hapag_pipeline')}
            disabled={isRunning || loading}
          >
            {t('initiateHapagWorkflow')}
          </button>
        </div>

        <div className="automation-buttons">
          <button
            type="button"
            className="btn-technical"
            onClick={() => setShowTechnicalDetails((prev) => !prev)}
          >
            {showTechnicalDetails ? t('hideTaskLogs') : t('showTaskLogs')}
          </button>
        </div>

        {error && <p className="automation-error">{error}</p>}

        {showTechnicalDetails && (
          <div className="automation-log-wrap">
            <h3>{t('taskLogsTitle')}</h3>
            <pre className="automation-log">
              {logs.length === 0
                ? t('noLogsYet')
                : logs.map((log) => `[${log.timestamp}] ${log.message}`).join('\n')}
            </pre>
          </div>
        )}
      </div>
    </section>
  );
};

export default AutomationPanel;

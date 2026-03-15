import React, { createContext, useContext, useState, useCallback } from 'react';

export type Language = 'en' | 'ko';

const translations = {
  en: {
    // App header / shell
    appTitle: 'Freight Route Analyzer',
    summary: 'Summary',
    showAutomationControl: 'Show Automation Control',
    hideAutomationControl: 'Hide Automation Control',
    oneWorkflowReadyHint: 'Run "Initiate ONE Workflow" in Automation Control to load fresh ONE route results.',
    hapagWorkflowReadyHint: 'Run "Initiate HAPAG Workflow" in Automation Control to load fresh HAPAG results.',
    summaryWorkflowReadyHint: 'Run ONE and/or HAPAG workflow first, then open Summary.',

    // Common
    loading: 'Loading...',
    apply: 'Apply',
    destination: 'Destination',
    containerType: 'Container Type',
    source: 'Source',
    sourceExcelApi: 'Excel (API)',
    rank: 'Rank',
    noData: 'No route data available for the selected criteria.',
    viaLabel: 'via',
    hapagOnlyTag: '(HAPAG only)',
    oneOnlyTag: '(ONE only)',
    notAvailable: 'N/A',

    // RouteDashboard
    oneRouteOptimizer: 'ONE Route Optimizer',
    routeSubtitle: 'Busan (KR) -> POD -> Inland Destination',
    transportMode: 'Transport Mode',
    remarks: 'Remarks',
    top3Routes: 'Top 3 Recommended Routes',
    routeComparison: 'Route Comparison on the Map',
    mapNote: '* map routes are for visualization purposes',
    highestCostRoute: 'Highest Cost Route',
    pod: 'POD (Intermediate Port)',
    inland: 'Inland',
    ocean: 'Ocean',
    totalRateEUR: 'Total Rate (EUR)',

    // HapagDashboard
    hapagRouteAnalyzer: 'HAPAG-LLOYD Route Analyzer',
    rateSummary: 'Rate Summary',
    chargeType: 'Charge Type',
    description: 'Description',
    rate: 'Rate',
    totalRate: 'Total Rate',
    moreDetails: 'More Details',
    chargeCategory: 'Charge Category',
    conversionRate: '*conversion rate 0.86',
    oceanFreight: 'Ocean Freight',
    destinationLandfreight: 'Destination Landfreight',
    otherCharges: 'Other Charges',

    // SummaryDashboard
    rateComparisonSummary: 'Rate Comparison Summary',
    comparingRoutes: 'Comparing ONE vs HAPAG-LLOYD Routes',
    bestRate: 'Best Rate',
    oneTop3: 'ONE - Top 3 Routes',
    inlandEUR: 'Inland (EUR)',
    oceanEUR: 'Ocean (EUR)',
    totalEUR: 'Total (EUR)',
    route: 'Route',
    eurEquivalent: 'EUR Equivalent',
    noOneRoutes: 'No ONE routes available',
    noHapagRoutes: 'No HAPAG routes available',

    // RouteMap / notes
    routeInformation: 'Route Information',
    viewInGoogleMaps: 'View in Google Maps',
    mapsCaption: 'Inline preview. Use the button for full directions.',
    rankRoute: 'Rank {rank} Route',
    routeFromTo: 'Route from {from} to {to}',
    podNoteBremerhaven: '* estimation based on Hamburg, Germany (freight cost unavailable)',
    podNoteSalerno: '* estimated based on Naples, Italy (freight cost unavailable)',

    // Automation
    automationControlTitle: 'Automation Control',
    statusLabel: 'Status',
    statusCode: '(code: {code})',
    onePipelineDestinationsLabel: 'ONE pipeline destinations (optional, one per line):',
    onePipelineDestinationsPlaceholder: 'If empty, it uses destinations.txt',
    initiateOneWorkflow: 'Initiate ONE Workflow',
    initiateHapagWorkflow: 'Initiate HAPAG Workflow',
    showTaskLogs: 'Show Task Logs',
    hideTaskLogs: 'Hide Task Logs',
    taskLogsTitle: 'Task Logs',
    noLogsYet: 'No logs yet.',
    automationSyncError: 'Failed to sync automation status.',
    automationStartError: 'Failed to start workflow.',
    progressReadyTitle: 'Ready to start',
    progressReadySubtitle: 'Click an Initiate button to begin the workflow.',
    progressOneCompletedTitle: 'ONE workflow completed',
    progressOneCompletedSubtitle: 'Fresh ONE route results are ready.',
    progressOneStoppedTitle: 'ONE workflow stopped early',
    progressOneStoppedSubtitle: 'Please retry the workflow. If it fails again, open task logs.',
    progressPreparingDestinationsTitle: 'Preparing destination data',
    progressPreparingDestinationsSubtitle: 'Checking destinations and location codes',
    progressDestinationsValidatedSubtitle: '{done}/{total} destinations validated',
    progressCollectingOneTitle: 'Collecting ONE inland rates',
    progressCollectingOneSubtitle: 'Scraping inland rates destination by destination',
    progressDestinationsScrapedSubtitle: '{done}/{total} destinations scraped',
    progressFinalizingTitle: 'Finalizing rankings and output',
    progressFinalizingSubtitle: 'Combining inland + ocean costs and generating final results',
    progressHapagCompletedTitle: 'HAPAG workflow completed',
    progressHapagCompletedSubtitle: 'Fresh HAPAG surcharge results are ready.',
    progressHapagStoppedTitle: 'HAPAG workflow stopped early',
    progressHapagStoppedSubtitle: 'Please retry the workflow. If it fails again, open task logs.',
    progressCollectingHapagTitle: 'Collecting HAPAG surcharges',
    progressPreparingExtractionSubtitle: 'Connecting and preparing destination extraction',
    progressDestinationsProcessedSubtitle: '{done}/{total} destinations processed',
    progressWorkflowInProgressTitle: 'Workflow in progress',
    progressPreparingWorkflowSubtitle: 'Preparing your workflow',

    // Chat
    chatGreeting: 'Hello, I am the PNS assistant.\nAsk me about rates, routes, and carrier comparisons.',
    chatFallbackError: 'Something went wrong.',
    chatServerError: 'Failed to reach the server. Please try again.',
    chatFabTitle: 'Freight Assistant',
    chatTitle: 'PNS Assistant',
    chatInputPlaceholder: 'Ask about routes, rates...',

    // Errors
    apiError: 'Failed to connect to API. Make sure the server is running.',
    selectDestination: 'Select a destination to view routes',

    // Language toggle
    langToggle: 'KOR',
  },
  ko: {
    // App header / shell
    appTitle: '해상 운임 분석기',
    summary: '요약',
    showAutomationControl: '자동화 제어 표시',
    hideAutomationControl: '자동화 제어 숨기기',
    oneWorkflowReadyHint: '최신 ONE 경로 결과를 불러오려면 자동화 제어에서 "ONE 워크플로 시작"을 실행하세요.',
    hapagWorkflowReadyHint: '최신 HAPAG 결과를 불러오려면 자동화 제어에서 "HAPAG 워크플로 시작"을 실행하세요.',
    summaryWorkflowReadyHint: '먼저 ONE 또는 HAPAG 워크플로를 실행한 뒤 요약 탭을 여세요.',

    // Common
    loading: '로딩 중...',
    apply: '적용',
    destination: '목적지',
    containerType: '컨테이너 유형',
    source: '출처',
    sourceExcelApi: '엑셀(API)',
    rank: '순위',
    noData: '선택한 조건에 해당하는 경로 데이터가 없습니다.',
    viaLabel: '경유',
    hapagOnlyTag: '(HAPAG 전용)',
    oneOnlyTag: '(ONE 전용)',
    notAvailable: '없음',

    // RouteDashboard
    oneRouteOptimizer: 'ONE 경로 최적화',
    routeSubtitle: '부산(KR) -> POD -> 내륙 목적지',
    transportMode: '운송 방식',
    remarks: '비고',
    top3Routes: '추천 경로 TOP 3',
    routeComparison: '지도 경로 비교',
    mapNote: '* 지도 경로는 시각화용입니다',
    highestCostRoute: '최고 비용 경로',
    pod: 'POD(중간 항구)',
    inland: '내륙',
    ocean: '해상',
    totalRateEUR: '총 운임(EUR)',

    // HapagDashboard
    hapagRouteAnalyzer: 'HAPAG-LLOYD 경로 분석',
    rateSummary: '운임 요약',
    chargeType: '요금 유형',
    description: '설명',
    rate: '운임',
    totalRate: '총 운임',
    moreDetails: '상세 정보',
    chargeCategory: '요금 항목',
    conversionRate: '*환율 0.86 적용',
    oceanFreight: '해상 운임',
    destinationLandfreight: '목적지 내륙 운임',
    otherCharges: '기타 요금',

    // SummaryDashboard
    rateComparisonSummary: '운임 비교 요약',
    comparingRoutes: 'ONE과 HAPAG-LLOYD 경로 비교',
    bestRate: '최저 운임',
    oneTop3: 'ONE - 추천 경로 TOP 3',
    inlandEUR: '내륙(EUR)',
    oceanEUR: '해상(EUR)',
    totalEUR: '합계(EUR)',
    route: '경로',
    eurEquivalent: 'EUR 환산',
    noOneRoutes: 'ONE 경로 데이터가 없습니다',
    noHapagRoutes: 'HAPAG 경로 데이터가 없습니다',

    // RouteMap / notes
    routeInformation: '경로 정보',
    viewInGoogleMaps: 'Google Maps에서 보기',
    mapsCaption: '인라인 미리보기입니다. 버튼을 눌러 전체 경로를 확인하세요.',
    rankRoute: '{rank}순위 경로',
    routeFromTo: '{from}에서 {to}까지 경로',
    podNoteBremerhaven: '* 함부르크(독일) 운임을 기준으로 추정한 값입니다(해당 항 운임 없음)',
    podNoteSalerno: '* 나폴리(이탈리아) 운임을 기준으로 추정한 값입니다(해당 항 운임 없음)',

    // Automation
    automationControlTitle: '자동화 제어',
    statusLabel: '상태',
    statusCode: '(코드: {code})',
    onePipelineDestinationsLabel: 'ONE 파이프라인 목적지(선택, 줄바꿈으로 구분):',
    onePipelineDestinationsPlaceholder: '비워두면 destinations.txt를 사용합니다',
    initiateOneWorkflow: 'ONE 워크플로 시작',
    initiateHapagWorkflow: 'HAPAG 워크플로 시작',
    showTaskLogs: '작업 로그 보기',
    hideTaskLogs: '작업 로그 숨기기',
    taskLogsTitle: '작업 로그',
    noLogsYet: '아직 로그가 없습니다.',
    automationSyncError: '자동화 상태를 동기화하지 못했습니다.',
    automationStartError: '워크플로 시작에 실패했습니다.',
    progressReadyTitle: '시작 준비 완료',
    progressReadySubtitle: '시작 버튼을 눌러 워크플로를 실행하세요.',
    progressOneCompletedTitle: 'ONE 워크플로 완료',
    progressOneCompletedSubtitle: '최신 ONE 경로 결과가 준비되었습니다.',
    progressOneStoppedTitle: 'ONE 워크플로가 중단되었습니다',
    progressOneStoppedSubtitle: '워크플로를 다시 실행하세요. 반복 실패 시 작업 로그를 확인하세요.',
    progressPreparingDestinationsTitle: '목적지 데이터 준비 중',
    progressPreparingDestinationsSubtitle: '목적지와 위치 코드를 확인하고 있습니다',
    progressDestinationsValidatedSubtitle: '{done}/{total} 목적지 검증 완료',
    progressCollectingOneTitle: 'ONE 내륙 운임 수집 중',
    progressCollectingOneSubtitle: '목적지별로 내륙 운임을 수집하고 있습니다',
    progressDestinationsScrapedSubtitle: '{done}/{total} 목적지 수집 완료',
    progressFinalizingTitle: '순위 계산 및 결과 생성 중',
    progressFinalizingSubtitle: '내륙+해상 비용을 결합해 최종 결과를 생성하고 있습니다',
    progressHapagCompletedTitle: 'HAPAG 워크플로 완료',
    progressHapagCompletedSubtitle: '최신 HAPAG 부대비용 결과가 준비되었습니다.',
    progressHapagStoppedTitle: 'HAPAG 워크플로가 중단되었습니다',
    progressHapagStoppedSubtitle: '워크플로를 다시 실행하세요. 반복 실패 시 작업 로그를 확인하세요.',
    progressCollectingHapagTitle: 'HAPAG 부대비용 수집 중',
    progressPreparingExtractionSubtitle: '연결 후 목적지 추출을 준비하고 있습니다',
    progressDestinationsProcessedSubtitle: '{done}/{total} 목적지 처리 완료',
    progressWorkflowInProgressTitle: '워크플로 진행 중',
    progressPreparingWorkflowSubtitle: '워크플로를 준비하고 있습니다',

    // Chat
    chatGreeting: '안녕하세요. PNS 어시스턴트입니다.\n운임, 경로, 선사 비교에 대해 물어보세요.',
    chatFallbackError: '문제가 발생했습니다.',
    chatServerError: '서버에 연결하지 못했습니다. 다시 시도해주세요.',
    chatFabTitle: '운임 도우미',
    chatTitle: 'PNS 어시스턴트',
    chatInputPlaceholder: '경로, 운임 등을 물어보세요...',

    // Errors
    apiError: 'API 연결에 실패했습니다. 서버 실행 상태를 확인하세요.',
    selectDestination: '경로를 보려면 목적지를 선택하세요',

    // Language toggle
    langToggle: 'ENG',
  },
} as const;

type TranslationKey = keyof typeof translations.en;

interface I18nContextType {
  lang: Language;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
  toggleLang: () => void;
}

const I18nContext = createContext<I18nContextType>({
  lang: 'en',
  t: (key: TranslationKey) => translations.en[key],
  toggleLang: () => {},
});

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<Language>('en');

  const toggleLang = useCallback(() => {
    setLang((prev) => (prev === 'en' ? 'ko' : 'en'));
  }, []);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      let text: string = translations[lang][key] || translations.en[key] || key;
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          text = text.replace(`{${k}}`, String(v));
        });
      }
      return text;
    },
    [lang]
  );

  return (
    <I18nContext.Provider value={{ lang, t, toggleLang }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => useContext(I18nContext);

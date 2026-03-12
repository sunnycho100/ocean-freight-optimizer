import React, { createContext, useContext, useState, useCallback } from 'react';

export type Language = 'en' | 'ko';

const translations = {
  en: {
    // App header
    appTitle: 'Freight Route Analyzer',
    summary: 'Summary',

    // Common
    loading: 'Loading...',
    apply: 'Apply',
    destination: 'Destination',
    containerType: 'Container Type',
    source: 'Source',
    rank: 'Rank',
    noData: 'No route data available for the selected criteria.',

    // RouteDashboard
    oneRouteOptimizer: 'ONE Route Optimizer',
    routeSubtitle: 'Busan (KR) → POD → Inland Destination',
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

    // RouteMap
    routeInformation: 'Route Information',
    viewInGoogleMaps: 'View in Google Maps',
    mapsCaption: 'Inline preview. Use the button for full directions.',
    rankRoute: 'Rank {rank} Route',

    // Errors
    apiError: 'Failed to connect to API. Make sure the server is running.',
    selectDestination: 'Select a destination to view routes',

    // Language toggle
    langToggle: 'KOR',
  },
  ko: {
    // App header
    appTitle: '해상 운임 분석기',
    summary: '비교 요약',

    // Common
    loading: '로딩 중...',
    apply: '적용',
    destination: '목적지',
    containerType: '컨테이너 유형',
    source: '출처',
    rank: '순위',
    noData: '선택한 조건에 해당하는 경로 데이터가 없습니다.',

    // RouteDashboard
    oneRouteOptimizer: 'ONE 경로 최적화',
    routeSubtitle: '부산 (KR) → POD → 내륙 목적지',
    transportMode: '운송 방식',
    remarks: '비고',
    top3Routes: '추천 경로 Top 3',
    routeComparison: '지도 경로 비교',
    mapNote: '* 지도 경로는 시각화 목적입니다',
    highestCostRoute: '최고 비용 경로',
    pod: 'POD (중간 항구)',
    inland: '내륙 운임',
    ocean: '해상 운임',
    totalRateEUR: '총 운임 (EUR)',

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

    // SummaryDashboard
    rateComparisonSummary: '운임 비교 요약',
    comparingRoutes: 'ONE vs HAPAG-LLOYD 경로 비교',
    bestRate: '최저 운임',
    oneTop3: 'ONE - 추천 경로 Top 3',
    inlandEUR: '내륙 (EUR)',
    oceanEUR: '해상 (EUR)',
    totalEUR: '합계 (EUR)',
    route: '경로',
    eurEquivalent: 'EUR 환산',
    noOneRoutes: 'ONE 경로 데이터 없음',
    noHapagRoutes: 'HAPAG 경로 데이터 없음',

    // RouteMap
    routeInformation: '경로 정보',
    viewInGoogleMaps: 'Google Maps에서 보기',
    mapsCaption: '미리보기입니다. 버튼을 눌러 상세 경로를 확인하세요.',
    rankRoute: '{rank}순위 경로',

    // Errors
    apiError: 'API 연결 실패. 서버가 실행 중인지 확인하세요.',
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

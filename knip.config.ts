import type { KnipConfig } from 'knip'

const config: KnipConfig = {
  entry: ['src/app.tsx'],
  project: ['src/**/*.{ts,tsx}'],
  ignore: [
    // shadcn/ui 컴포넌트는 라이브러리 패턴으로 일부 export가 현재 미사용이어도 유지
    'src/components/ui/**',
  ],
  ignoreDependencies: [
    'tailwindcss', // used via @tailwindcss/vite plugin
    // pnpm vitest run --coverage 에서 사용
    '@vitest/coverage-v8',
  ],
}

export default config

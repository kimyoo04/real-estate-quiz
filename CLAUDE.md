# CertiPass — Claude Code 지침

## 커밋·푸시 전 필수 검증

**git push 전에 반드시 아래 순서로 검증하고, 에러가 없을 때만 push한다:**

```bash
pnpm lint          # ESLint 검사
pnpm tsc --noEmit  # TypeScript 타입 검사
pnpm build         # Vite 빌드 (CI와 동일 환경)
```

에러가 발생하면 push하지 말고 먼저 수정한다.

> 이유: CI는 `pnpm build`를 실행하므로 TypeScript strict 모드 에러가
> 로컬 `tsc --noEmit`에서 통과해도 빌드에서 실패할 수 있다.

## 브랜치 규칙

- 작업은 `main` 브랜치에서 직접 커밋·푸시
- `dev` 브랜치 등 다른 브랜치로 push하지 않는다

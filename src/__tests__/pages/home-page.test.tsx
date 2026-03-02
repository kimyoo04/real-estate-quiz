import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { HomePage } from '@/pages/home-page'

import { renderWithRoute } from '../helpers/render-with-route'

const MOCK_EXAMS = [
  { id: 'realtor', name: '공인중개사', description: '공인중개사 자격시험 대비', isActive: true },
  { id: 'appraiser', name: '감정평가사', description: '감정평가사 자격시험 대비', isActive: false },
]

describe('HomePage', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      json: () => Promise.resolve(MOCK_EXAMS),
    } as Response)
  })

  function renderHomePage() {
    return renderWithRoute(<HomePage />, {
      route: '/',
      path: '/',
    })
  }

  it('renders exam list after loading', async () => {
    renderHomePage()

    await waitFor(() => {
      expect(screen.getByText('공인중개사')).toBeInTheDocument()
    })
    expect(screen.getByText('감정평가사')).toBeInTheDocument()
  })

  it('shows active badge for active exams', async () => {
    renderHomePage()

    await waitFor(() => {
      expect(screen.getByText('학습 가능')).toBeInTheDocument()
    })
    expect(screen.getByText('준비 중')).toBeInTheDocument()
  })

  it('shows inactive exam with reduced opacity', async () => {
    renderHomePage()

    await waitFor(() => {
      expect(screen.getByText('감정평가사')).toBeInTheDocument()
    })

    const inactiveCard = screen.getByText('감정평가사').closest('[data-slot="card"]')
    expect(inactiveCard?.className).toContain('opacity-50')
  })

  it('active exam card is clickable', async () => {
    const user = userEvent.setup()
    renderHomePage()

    await waitFor(() => {
      expect(screen.getByText('공인중개사')).toBeInTheDocument()
    })

    const card = screen.getByText('공인중개사').closest('[data-slot="card"]')!
    // Should not throw on click
    await user.click(card)
  })

  it('renders page description text', async () => {
    renderHomePage()

    expect(screen.getByText('자격증을 선택하여 학습을 시작하세요')).toBeInTheDocument()
  })
})

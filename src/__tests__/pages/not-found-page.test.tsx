import { screen } from '@testing-library/react'

import { NotFoundPage } from '@/pages/not-found-page'

import { renderWithRoute } from '../helpers/render-with-route'

describe('NotFoundPage', () => {
  function renderNotFound() {
    return renderWithRoute(<NotFoundPage />, {
      route: '/some-nonexistent-path',
      path: '*',
    })
  }

  it('renders 404 text', () => {
    renderNotFound()

    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('shows descriptive message', () => {
    renderNotFound()

    expect(screen.getByText('요청하신 페이지가 존재하지 않습니다')).toBeInTheDocument()
  })

  it('shows home navigation button', () => {
    renderNotFound()

    expect(screen.getByRole('button', { name: '홈으로 돌아가기' })).toBeInTheDocument()
  })
})

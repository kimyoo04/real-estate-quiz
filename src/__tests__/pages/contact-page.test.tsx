import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ContactPage } from '@/pages/contact-page'

import { renderWithRoute } from '../helpers/render-with-route'

vi.mock('@emailjs/browser', () => ({
  default: {
    send: vi.fn().mockResolvedValue({ status: 200 }),
  },
}))

describe('ContactPage', () => {
  function renderContact() {
    return renderWithRoute(<ContactPage />, {
      route: '/contact',
      path: '/contact',
    })
  }

  it('renders contact form fields', () => {
    renderContact()

    expect(screen.getByLabelText('이름')).toBeInTheDocument()
    expect(screen.getByLabelText('이메일')).toBeInTheDocument()
    expect(screen.getByLabelText('메시지')).toBeInTheDocument()
  })

  it('renders submit button', () => {
    renderContact()

    expect(screen.getByRole('button', { name: /전송하기/ })).toBeInTheDocument()
  })

  it('allows filling in form fields', async () => {
    const user = userEvent.setup()
    renderContact()

    const nameInput = screen.getByLabelText('이름')
    const emailInput = screen.getByLabelText('이메일')
    const messageInput = screen.getByLabelText('메시지')

    await user.type(nameInput, '홍길동')
    await user.type(emailInput, 'test@example.com')
    await user.type(messageInput, '테스트 메시지')

    expect(nameInput).toHaveValue('홍길동')
    expect(emailInput).toHaveValue('test@example.com')
    expect(messageInput).toHaveValue('테스트 메시지')
  })

  it('shows success message after submission', async () => {
    const user = userEvent.setup()
    renderContact()

    await user.type(screen.getByLabelText('이름'), '홍길동')
    await user.type(screen.getByLabelText('이메일'), 'test@example.com')
    await user.type(screen.getByLabelText('메시지'), '테스트')

    await user.click(screen.getByRole('button', { name: /전송하기/ }))

    expect(await screen.findByText(/성공적으로 전송/)).toBeInTheDocument()
  })

  it('shows error message on submission failure', async () => {
    const emailjs = await import('@emailjs/browser')
    vi.mocked(emailjs.default.send).mockRejectedValueOnce(new Error('fail'))

    const user = userEvent.setup()
    renderContact()

    await user.type(screen.getByLabelText('이름'), '홍길동')
    await user.type(screen.getByLabelText('이메일'), 'test@example.com')
    await user.type(screen.getByLabelText('메시지'), '테스트')

    await user.click(screen.getByRole('button', { name: /전송하기/ }))

    expect(await screen.findByText(/실패/)).toBeInTheDocument()
  })
})

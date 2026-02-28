import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ResultPage } from "@/pages/ResultPage";
import { useQuizStore } from "@/stores/useQuizStore";
import { renderWithRoute, ROUTES, basePath, chapterKey } from "../helpers/renderWithRoute";
import { PROGRESS_MIXED, PROGRESS_ALL_CORRECT } from "../helpers/mockData";
import type { ChapterProgress } from "@/types";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

function renderResult(search?: string) {
  return renderWithRoute(<ResultPage />, {
    route: `${basePath()}/result`,
    path: ROUTES.result,
    search,
  });
}

describe("ResultPage", () => {
  it("displays score percentage", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=quiz");

    // 1 correct out of 3 total = 33%
    expect(screen.getByText("33점")).toBeInTheDocument();
  });

  it("shows correct and wrong counts", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=quiz");

    // In the detail stats cards
    expect(screen.getByText("1")).toBeInTheDocument(); // correct count
    expect(screen.getByText("2")).toBeInTheDocument(); // wrong count
    expect(screen.getByText("정답")).toBeInTheDocument();
    expect(screen.getByText("오답")).toBeInTheDocument();
  });

  it("shows trophy emoji for 100% score", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_ALL_CORRECT },
    });

    renderResult("?mode=quiz");

    expect(screen.getByText("🏆")).toBeInTheDocument();
    expect(screen.getByText("100점")).toBeInTheDocument();
  });

  it("shows celebration emoji for 70%+ score", () => {
    const progress: ChapterProgress = {
      correctIds: ["q_004", "q_005", "q_006"],
      wrongIds: ["q_008"],
      revealedIds: [],
      totalMc: 4,
      totalBlank: 0,
    };
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: progress },
    });

    renderResult("?mode=quiz");

    expect(screen.getByText("🎉")).toBeInTheDocument();
    expect(screen.getByText("75점")).toBeInTheDocument();
  });

  it("shows strength emoji for 40%+ score", () => {
    const progress: ChapterProgress = {
      correctIds: ["q_004"],
      wrongIds: ["q_005"],
      revealedIds: [],
      totalMc: 2,
      totalBlank: 0,
    };
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: progress },
    });

    renderResult("?mode=quiz");

    expect(screen.getByText("💪")).toBeInTheDocument();
  });

  it("shows study emoji for <40% score", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=quiz");

    expect(screen.getByText("📚")).toBeInTheDocument();
  });

  it("shows '오답만 다시 풀기' only when wrong > 0", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=quiz");

    expect(screen.getByText(/오답만 다시 풀기/)).toBeInTheDocument();
  });

  it("hides '오답만 다시 풀기' when no wrongs", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_ALL_CORRECT },
    });

    renderResult("?mode=quiz");

    expect(screen.queryByText(/오답만 다시 풀기/)).not.toBeInTheDocument();
  });

  it("shows different button text for wrong mode", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=wrong");

    expect(screen.getByText("전체 문제 풀기")).toBeInTheDocument();
  });

  it("shows '처음부터 다시 풀기' in quiz mode", () => {
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=quiz");

    expect(screen.getByText("처음부터 다시 풀기")).toBeInTheDocument();
  });

  it("reset button calls resetChapterProgress", async () => {
    const user = userEvent.setup();
    useQuizStore.setState({
      chapterProgress: { [chapterKey()]: PROGRESS_MIXED },
    });

    renderResult("?mode=quiz");

    await user.click(screen.getByText("진도 초기화 후 과목 선택으로"));

    expect(useQuizStore.getState().chapterProgress[chapterKey()]).toBeUndefined();
    expect(mockNavigate).toHaveBeenCalled();
  });

  it("handles zero total without division error", () => {
    renderResult("?mode=quiz");

    expect(screen.getByText("0점")).toBeInTheDocument();
    expect(screen.getByText("0문제 중 0문제 정답")).toBeInTheDocument();
  });
});

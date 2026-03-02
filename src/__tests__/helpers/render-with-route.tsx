/* eslint-disable react-refresh/only-export-components */
import { render } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import type { ReactElement } from "react";

export const ROUTES = {
  quiz: "/exam/:examId/study/:subjectId/:chapterId/quiz",
  blank: "/exam/:examId/study/:subjectId/:chapterId/blank",
  result: "/exam/:examId/study/:subjectId/:chapterId/result",
  studyMode: "/exam/:examId/study/:subjectId/:chapterId",
} as const;

export const TEST_PARAMS = {
  examId: "realtor",
  subjectId: "sub_1",
  chapterId: "ch_1",
};

export function basePath() {
  return `/exam/${TEST_PARAMS.examId}/study/${TEST_PARAMS.subjectId}/${TEST_PARAMS.chapterId}`;
}

export function chapterKey() {
  return `${TEST_PARAMS.examId}/${TEST_PARAMS.subjectId}/${TEST_PARAMS.chapterId}`;
}

interface RenderWithRouteOptions {
  route: string;
  path: string;
  search?: string;
}

export function renderWithRoute(
  ui: ReactElement,
  { route, path, search }: RenderWithRouteOptions
) {
  const initialEntry = search ? `${route}${search}` : route;

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path={path} element={ui} />
      </Routes>
    </MemoryRouter>
  );
}

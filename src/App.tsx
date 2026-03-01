import { HashRouter, Routes, Route } from "react-router-dom";
import { HomePage } from "@/pages/HomePage";
import { SubjectPage } from "@/pages/SubjectPage";
import { StudyModePage } from "@/pages/StudyModePage";
import { FillBlankPage } from "@/pages/FillBlankPage";
import { QuizPage } from "@/pages/QuizPage";
import { ResultPage } from "@/pages/ResultPage";
import { TreeSubjectListPage } from "@/pages/TreeSubjectListPage";
import { TreeViewPage } from "@/pages/TreeViewPage";
import { ClassifyPage } from "@/pages/ClassifyPage";
import { MockExamPage } from "@/pages/MockExamPage";
import { MockExamResultPage } from "@/pages/MockExamResultPage";
import { DashboardPage } from "@/pages/DashboardPage";

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/exam/:examId" element={<SubjectPage />} />
        <Route path="/exam/:examId/dashboard" element={<DashboardPage />} />
        <Route path="/exam/:examId/tree" element={<TreeSubjectListPage />} />
        <Route path="/exam/:examId/tree/:subjectId" element={<TreeViewPage />} />
        <Route path="/exam/:examId/classify/:subjectId" element={<ClassifyPage />} />
        <Route path="/exam/:examId/mock/:subjectId" element={<MockExamPage />} />
        <Route path="/exam/:examId/mock/:subjectId/result" element={<MockExamResultPage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId" element={<StudyModePage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId/blank" element={<FillBlankPage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId/quiz" element={<QuizPage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId/result" element={<ResultPage />} />
      </Routes>
    </HashRouter>
  );
}

export default App;

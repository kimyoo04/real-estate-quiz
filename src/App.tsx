import { HashRouter, Routes, Route } from "react-router-dom";
import { HomePage } from "@/pages/HomePage";
import { SubjectPage } from "@/pages/SubjectPage";
import { StudyModePage } from "@/pages/StudyModePage";
import { FillBlankPage } from "@/pages/FillBlankPage";
import { QuizPage } from "@/pages/QuizPage";

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/exam/:examId" element={<SubjectPage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId" element={<StudyModePage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId/blank" element={<FillBlankPage />} />
        <Route path="/exam/:examId/study/:subjectId/:chapterId/quiz" element={<QuizPage />} />
      </Routes>
    </HashRouter>
  );
}

export default App;

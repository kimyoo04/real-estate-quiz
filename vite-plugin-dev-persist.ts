import type { Plugin } from "vite";
import fs from "node:fs";
import path from "node:path";

export function devPersistPlugin(): Plugin {
  const publicDataDir = path.resolve(process.cwd(), "public/data/");

  function assertSafePath(filePath: string): string {
    const resolved = path.resolve(publicDataDir, filePath);
    if (!resolved.startsWith(publicDataDir + path.sep) && resolved !== publicDataDir) {
      throw new Error(`Path traversal blocked: ${filePath}`);
    }
    return resolved;
  }

  return {
    name: "vite-plugin-dev-persist",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use("/__dev-api/write-json", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end("Method not allowed");
          return;
        }

        let body = "";
        req.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        req.on("end", () => {
          try {
            const { filePath, data } = JSON.parse(body) as {
              filePath: string;
              data: unknown;
            };

            const absPath = assertSafePath(filePath);
            const dir = path.dirname(absPath);
            if (!fs.existsSync(dir)) {
              fs.mkdirSync(dir, { recursive: true });
            }

            fs.writeFileSync(absPath, JSON.stringify(data, null, 2) + "\n", "utf-8");

            res.setHeader("Content-Type", "application/json");
            res.statusCode = 200;
            res.end(JSON.stringify({ ok: true }));
          } catch (err) {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: String(err) }));
          }
        });
      });

      server.middlewares.use("/__dev-api/patch-questions", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end("Method not allowed");
          return;
        }

        let body = "";
        req.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        req.on("end", () => {
          try {
            const { subjectDir, questionEdits } = JSON.parse(body) as {
              subjectDir: string;
              questionEdits: Record<string, Record<string, unknown>>;
            };

            const absDir = assertSafePath(subjectDir);
            if (!fs.existsSync(absDir) || !fs.statSync(absDir).isDirectory()) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: `Not a directory: ${subjectDir}` }));
              return;
            }

            const quizFiles = fs
              .readdirSync(absDir)
              .filter((f) => f.endsWith("_quiz.json"));

            let patchedCount = 0;
            for (const file of quizFiles) {
              const filePath = path.join(absDir, file);
              const raw = fs.readFileSync(filePath, "utf-8");
              const questions = JSON.parse(raw) as Array<Record<string, unknown>>;
              let changed = false;

              for (const q of questions) {
                const id = q.id as string;
                if (questionEdits[id]) {
                  Object.assign(q, questionEdits[id]);
                  changed = true;
                  patchedCount++;
                }
              }

              if (changed) {
                fs.writeFileSync(filePath, JSON.stringify(questions, null, 2) + "\n", "utf-8");
              }
            }

            res.setHeader("Content-Type", "application/json");
            res.statusCode = 200;
            res.end(JSON.stringify({ ok: true, patchedCount }));
          } catch (err) {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: String(err) }));
          }
        });
      });
    },
  };
}

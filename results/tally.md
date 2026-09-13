task_id | condition | rep | outcome | iterations | wall_clock_s | tokens_in | tokens_out | baseline | full_suite | note
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
T04 | MA | rep2 | pass_at_cap | 26 | 1837 | 274132 | 20725 | FAIL | FAIL | Coder said DONE at iter 25; harness cap-check bug
T01 | SA | rep1 | pass | 17 | 886 | 70380 | 2432 | FAIL | FAIL | pilot
T01 | MA | rep1 | pass | 9 | 3816 | 33934 | 9115 | FAIL | FAIL | pilot
T04 | SA | rep1 | pass | 16 | 899 | 67006 | 2498 | FAIL | FAIL | pilot
T04 | MA | rep1 | fail_iteration_cap | 12 | 312 | 109286 | 3501 | FAIL | FAIL | pilot; Coder blind before MA harness fix
T01 | SA | rep2 | pass | 14 | 953 | 61318 | 2207 | FAIL | FAIL | operator hit f early when oracle passed
T01 | MA | rep2 | pass | 24 | 1305 | 171950 | 11577 | FAIL | FAIL | full-run start
T04 | SA | rep2 | pass | 15 | 517 | 43945 | 984 | FAIL | FAIL | full-run start; oracle 27/27 pass
T02 | MA | rep1 | pass | 19 | 664 | 104811 | 14065 | FAIL | PASS | full-run
T02 | SA | rep1 | fail_iteration_cap | 25 | 568 | 110765 | 5025 | FAIL | FAIL | iteration cap
T02 | MA | rep2 | pass | 10 | 257 | 47747 | 8285 | FAIL | PASS | full-run
T02 | SA | rep2 | pass | 23 | 1277 | 125765 | 5782 | FAIL | PASS | full-run
T03 | SA | rep1 | pass | 24 | 828 | 189765 | 3922 | FAIL | FAIL | full-run
T03 | MA | rep1 | pass | 11 | 256 | 39648 | 7629 | FAIL | FAIL | full-run
T03 | SA | rep2 | pass | 18 | 501 | 157471 | 2289 | FAIL | FAIL | full-run
T03 | MA | rep2 | pass | 9 | 363 | 28750 | 10653 | FAIL | FAIL | full-run
T05 | SA | rep1 | pass | 16 | 393 | 42174 | 1124 | FAIL | PASS | full-run
T05 | MA | rep1 | pass | 15 | 426 | 88987 | 8908 | FAIL | PASS | full-run
T05 | SA | rep2 | pass | 12 | 309 | 30057 | 2601 | FAIL | PASS | full-run
T05 | MA | rep2 | pass | 12 | 180 | 36751 | 5866 | FAIL | PASS | full-run
T06 | SA | rep1 | fail_iteration_cap | 26 | 1099 | 263502 | 37260 | FAIL | FAIL | iteration cap
T06 | MA | rep1 | fail_iteration_cap | 26 | 1099 | 263502 | 37260 | FAIL | FAIL | iteration cap
T06 | SA | rep2 | abort | 25 | 787 | 149367 | 1938 | FAIL | FAIL | abort
T06 | MA | rep2 | abort_coder | 26 | 10194 | 269762 | 34883 | FAIL | FAIL | abort_coder
T07 | MA | rep1 | pass | 8 | 187 | 18066 | 9045 | FAIL | PASS | full-run
T07 | SA | rep2 | pass | 9 | 329 | 21016 | 1135 | FAIL | PASS | full-run
T07 | MA | rep2 | pass | 9 | 154 | 21463 | 5267 | FAIL | PASS | full-run
T07 | SA | rep1 | pass | 12 | 10895 | 36270 | 1293 | FAIL | PASS | full-run
T08 | SA | rep1 | abort | 25 | 782 | 299539 | 11596 | FAIL | FAIL | abort
T08 | MA | rep1 | abort_coder | 21 | 46538 | 321248 | 39867 | FAIL | FAIL | abort_coder
T08 | SA | rep2 | pass | 25 | 1999 | 439067 | 16731 | FAIL | PASS | full-run
T08 | MA | rep2 | abort_coder | 24 | 6841 | 251419 | 48028 | FAIL | FAIL | abort_coder
T10 | SA | rep1 | pass | 13 | 224 | 61182 | 1578 | FAIL | FAIL | full-run
T10 | MA | rep1 | pass | 12 | 223 | 45638 | 7365 | FAIL | FAIL | full-run
T10 | SA | rep2 | pass | 11 | 190 | 30019 | 780 | FAIL | FAIL | full-run
T10 | MA | rep2 | pass | 11 | 217 | 42095 | 7212 | FAIL | FAIL | full-run
T12 | SA | rep1 | pass | 23 | 515 | 146982 | 5412 | FAIL | FAIL | full-run
T12 | MA | rep1 | pass | 21 | 513 | 150137 | 23851 | FAIL | FAIL | full-run
T12 | SA | rep2 | pass | 24 | 581 | 197412 | 5117 | FAIL | FAIL | full-run
T12 | MA | rep2 | pass | 14 | 462 | 53218 | 16911 | FAIL | FAIL | full-run
T13 | SA | rep1 | fail_iteration_cap | 25 | 671 | 232035 | 16636 | FAIL | FAIL | iteration cap
T13 | MA | rep1 | pass | 21 | 1234 | 217806 | 20534 | FAIL | FAIL | full-run
T13 | SA | rep2 | pass | 22 | 601 | 222158 | 11801 | FAIL | FAIL | full-run
T13 | MA | rep2 | abort_coder | 19 | 819 | 170880 | 38928 | FAIL | FAIL | abort_coder
T15 | SA | rep1 | pass | 11 | 190 | 31121 | 1147 | FAIL | PASS | full-run
T15 | MA | rep1 | pass | 8 | 219 | 22834 | 6657 | FAIL | PASS | full-run
T15 | SA | rep2 | pass | 13 | 254 | 48157 | 1358 | FAIL | PASS | full-run
T15 | MA | rep2 | pass | 7 | 150 | 15525 | 6281 | FAIL | PASS | full-run

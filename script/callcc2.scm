(define cc #f)

(define (something)
  (display (+ 5 (call/cc
                  (lambda (k)
                    (set! cc k)
                    8))))
  (newline))

(something)
(cc 0)

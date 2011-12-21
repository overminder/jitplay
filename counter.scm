
(define (make-counter)
  (define a 0)
  (lambda ()
    (set! a (+ a 1))
    a))

(define c (make-counter))
(display (c))
(newline)
(display (c))
(newline)

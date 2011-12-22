;; This loop is 5x faster than guile, but tree recursion is much slower...
;; This means that virtualized stack is extremely fast and is capable
;; of recongizing tailcalls as loop, nice.
;;
;; However for non-tail-recursive function, performance degrades rapidly.

(define (sum n s)
  (if (< n 1) s
      (sum (- n 1) (+ s n))))

(display (sum 20000000 0))
(newline)


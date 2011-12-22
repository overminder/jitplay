(define (for-each proc lst)
  (if (null? lst) #f
      (begin
        (proc (car lst))
        (for-each proc (cdr lst)))))

(define (prn x)
  (display x)
  (newline))

(define (generate-one-element-at-a-time lst)
 
  ;; Hand the next item from a-list to "return" or an end-of-list marker
  (define (control-state return)
    (prn return)
    (for-each 
      (lambda (element)
        (set! return (call/cc
                       (lambda (resume-here)
                         ;; Grab the current continuation
                        (set! control-state resume-here)
                        (return element)))))
      lst)
    (return 'you-fell-off-the-end))
 
  ;; (-> X u 'you-fell-off-the-end)
  ;; This is the actual generator, producing one item from a-list at a time
  (lambda ()
    (call/cc control-state)))
 
(define generate-digit
  (generate-one-element-at-a-time '(0 1 2 3 4 5 6 7 8 9)))
 
(display (generate-digit))
(newline)
(display (generate-digit))
(newline)


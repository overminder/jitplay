
(define (for-each proc lst)
  (if (null? lst) #f
      (begin
        (proc (car lst))
        (for-each proc (cdr lst)))))

(define (prn x)
  (display x)
  (newline))

(define (assoc key alist)
  (call/cc
    (lambda (return)
      (for-each (lambda (item)
                  (if (equal? (car item) key)
                      (return item)))
                alist)
      #f)))

(define alist '((a 1) (b 2) (c 3)))
(display (assoc 'd alist))
(newline)


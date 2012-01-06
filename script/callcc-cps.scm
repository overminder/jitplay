(define mycall/cc
  (lambda (func cont)
    (func (lambda ($Rv $Ignore)
            (cont $Rv))
          cont)))

(define myfor-each
  (lambda (proc lst cont)
    (if (null? lst) (cont #f)
        (begin
          (proc (car lst)
            (lambda ($Ignore)
              (myfor-each proc (cdr lst) cont)))))))

(define generate-one-element-at-a-time
  (lambda (lst $Cont)
 
  ;; Hand the next item from a-list to "return" or an end-of-list marker
    (define control-state #f)
    ((lambda ($Ign)
      ($Cont
        (lambda ($Cont5)
          (mycall/cc control-state $Cont5))))
      (set! control-state
        (lambda (return $Cont2)
          (myfor-each 
            (lambda (element $Cont3)
              (mycall/cc
                (lambda (resume-here $Cont4)
                  (set! control-state resume-here)
                  (return element $Cont4))
                (lambda ($Rv)
                  ($Cont3 (set! return $Rv)))))
            lst
            (lambda ($Ignore)
              (return 'you-fell-off-the-end $Cont2))))))))
   
    ;; (-> X u 'you-fell-off-the-end)
    ;; This is the actual generator, producing one item from a-list at a time
 
(define gen-digit #f)
(generate-one-element-at-a-time '(0 1 2)
  (lambda ($Rv)
    (set! gen-digit $Rv)))

(gen-digit (lambda (x) (display x) (newline)))
(gen-digit (lambda (x) (display x) (newline)))
(gen-digit (lambda (x) (display x) (newline)))
(gen-digit (lambda (x) (display x) (newline)))


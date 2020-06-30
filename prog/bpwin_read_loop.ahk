; loops reads in BPWin GUI
; displays results and logs dumps to file
; alt a to activate
; shift to stop
!a::

loopi := 0

FormatTime, CurrentDateTime,, yyyy-MM-dd_HH.mm.ss
basedir = D:\buffer\rom\ahk\out
dirout = %basedir%\%CurrentDateTime%
; MsgBox %dirout%
FileCreateDir, %dirout%

Loop {
	;initiate read
	send {SPACE}
	Sleep, 2000

	
	; clear abnormal condition (if any)
	; ex: overcurrent during read
	Send {Esc}
	Sleep, 200
	
	
	; activate data view
	send ^e
	; select hex view
	Loop, 7 {
		send {Tab}
	}
	send {Up}
	; let user oogle the data
	Sleep, 2000
	; Close hex view
	Send {Esc}


	Sleep, 200


	; file => save pattern as
	; activate file menu
	; send !f
	Send {Alt}
	Send {Down}
	Send {Down}
	Send {Down}
	Send {Down}
	send {Enter}
	; save dialogue
	Sleep, 200
	loops := Format("{:04}", loopi)
	fn = %dirout%\%loops%.bin
	Send %fn%
	send {Enter}
	; file format options: accept deafult
	send {Enter}

	
	Sleep, 200

	loopi := loopi + 1
	;MsgBox, %loopi%
}




; this makes it so if you press escape, it stops the script, good for infinite loops
; supposedly you keep this at the bottom of the file per stackoverflow
; interfering with closing message boxes
; Esc::ExitApp
; harmless key
Shift::ExitApp

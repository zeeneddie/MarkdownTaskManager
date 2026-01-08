Imports System

Public Class Calculator
    Private _value As Integer
    
    Public Sub New()
        _value = 0
    End Sub
    
    Public Function Add(ByVal x As Integer, ByVal y As Integer) As Integer
        Return x + y
    End Function
End Class

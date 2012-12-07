using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

public static class utils
{
    public static T StringToEnum<T>(string name)
    {
        return (T)Enum.Parse(typeof(T), name);
    }
}

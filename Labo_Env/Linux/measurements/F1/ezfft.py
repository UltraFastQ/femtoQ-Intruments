def ezfft(t, S, normalization = "ortho", neg = False):
    """ Returns the Fourier transform of S and the frequency vector associated with it"""
    import numpy as np
    y = np.fft.fft(S,norm=normalization)
    y = np.fft.fftshift(y)
    f = np.fft.fftfreq(t.shape[-1], d = t[2]-t[1])
    f = np.fft.fftshift(f)
    if neg == False:
        y = 2*y[f>0]
        f = f[f>0]
    return f,y


def ezifft(f, y, normalization = "ortho"):
    '''Returns the inverse Fourier transform of y and the time vector associatedwith it
    WARNING : the negative frequencies must be included in the y vector'''
    import numpy as np
    fstep = f[1]-f[0]
    N = len(f)
    tstep = 1/(N*(f[2]-f[1]))
    x = np.linspace(-int(N*tstep/2),int(N*tstep/2),N)
    y = np.fft.ifftshift(y)
    S = np.fft.ifft(y,norm=normalization)
    return x,S

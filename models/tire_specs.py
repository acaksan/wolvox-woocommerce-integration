from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class TireSize:
    id: int
    width: int          # Genişlik (mm)
    aspect_ratio: int   # Yanak yüksekliği (%)
    construction: str   # Yapı (R: Radyal)
    diameter: int       # Çap (inç)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

@dataclass
class TireSeason:
    id: int
    name: str          # Yaz, Kış, 4 Mevsim
    code: str          # S: Summer, W: Winter, A: All Season
    description: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

@dataclass
class SpeedRating:
    id: int
    code: str          # H, V, W, Y vb.
    speed: int         # Maksimum hız (km/h)
    description: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

@dataclass
class LoadIndex:
    id: int
    code: int          # 91, 94 vb.
    weight: int        # Maksimum yük (kg)
    description: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

@dataclass
class TireSpecs:
    id: int
    stok_kodu: str     # Wolvox stok kodu
    size: TireSize
    season: TireSeason
    speed_rating: SpeedRating
    load_index: LoadIndex
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    def get_full_size(self) -> str:
        """Lastiğin tam ebat kodunu döndürür (örn: 205/55R16)"""
        return f"{self.size.width}/{self.size.aspect_ratio}{self.size.construction}{self.size.diameter}"

    def get_full_specs(self) -> str:
        """Lastiğin tam özelliklerini döndürür (örn: 205/55R16 91H)"""
        return f"{self.get_full_size()} {self.load_index.code}{self.speed_rating.code}"

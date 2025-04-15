from typing import Dict, Any, List

class DataExtractor:
    """
    数据提取基类，负责从搜索结果中提取结构化数据

    Attributes:
        raw_data (Dict[str, Any]): 原始数据
    """

    def __init__(self, raw_data: Dict[str, Any]):
        """
        初始化数据提取实例

        Args:
            raw_data (Dict[str, Any]): 原始数据
        """
        self.raw_data = raw_data

    def extract(self) -> Dict[str, Any]:
        """
        提取结构化数据

        Returns:
            Dict[str, Any]: 提取后的结构化数据
        """
        raise NotImplementedError("子类必须实现此方法")

    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗和格式化数据

        Args:
            data (Dict[str, Any]): 待清洗的数据

        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        raise NotImplementedError("子类必须实现此方法")

    def batch_extract(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量提取数据

        Args:
            data_list (List[Dict[str, Any]]): 原始数据列表

        Returns:
            List[Dict[str, Any]]: 提取后的数据列表
        """
        return [self.extract(data) for data in data_list]
